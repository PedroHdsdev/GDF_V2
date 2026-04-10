"""
Comunicação RFC com SAP usando a tabela SapConnection.

Padrão de uso para cada função SAP via RFC:
  1. Crie um método com o nome da funcionalidade (ex: importar_custo_cliente).
  2. Esse método chama o responsável pela conexão (SapRfc.call ou SapRfc.with_connection).
  3. Chame a função RFC passando os parâmetros.
  4. A comunicação é fechada ao final (SapRfc.call já abre, chama e fecha).

Exemplo: ver importar_custo_cliente, importar_relatorio_custo, consultar_balanco_financeiro (ZF_ECF01).
"""
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

PYRFC_IMPORT_ERROR: str = ""

try:
    from pyrfc import Connection as PyRfcConnection

    PYRFC_AVAILABLE = True
except Exception as _pyrfc_exc:
    PyRfcConnection = None
    PYRFC_AVAILABLE = False
    PYRFC_IMPORT_ERROR = str(_pyrfc_exc).strip() or repr(_pyrfc_exc)

_RFC_BALANCO_FINANCEIRO = "ZF_ECF01"

# Limite dos números em I_MONTH_B / I_MONTH_V e largura máxima do intervalo (inclusive).
_ZF_ECF01_MAX_NUMERO_PERIODO: int = 99
_ZF_ECF01_MAX_INTERVALO_PERIODOS: int = 120

# Colunas lógicas do JSON em R_RETURN (lista / árvore de nós).
ZF_ECF01_ARVORE_COLUNAS: Tuple[str, ...] = ("id", "conta", "text", "valor", "children")


def _zf_ecf01_ler_conta(item: Dict[str, Any]) -> str:
    """Número da conta SAP (ex.: 0011110001); aceita conta / CONTA / SAKNR.

    Na estrutura atual do JSON em R_RETURN, o código da linha na hierarquia costuma vir
    em ``id``; ``racct`` fica nas subcontas dentro de ``accounts`` — não usar ``racct`` aqui.
    """
    for k in ("conta", "CONTA", "Conta", "SAKNR", "saknr"):
        if k in item and item.get(k) is not None:
            s = str(item.get(k)).strip()
            if s:
                return s
    nid = item.get("id")
    if nid is not None:
        s = str(nid).strip()
        if s:
            return s
    return ""


def _zf_ecf01_ler_texto_no(item: Dict[str, Any]) -> str:
    """Descrição do nó: ``text`` (árvore recursiva ABAP), ``txt_balance`` (lista plana), etc."""
    for k in ("text", "TEXT", "Text", "txt_balance", "TXT_BALANCE", "TxtBalance"):
        if k in item and item.get(k) is not None:
            return str(item.get(k)).strip()
    return ""


def _zf_ecf01_ler_stufe(item: Dict[str, Any]) -> Optional[int]:
    v = item.get("stufe")
    if v is None:
        v = item.get("STUFE")
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _zf_ecf01_normalizar_accounts_list(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for acc in raw:
        if not isinstance(acc, dict):
            continue
        parsed = _zf_ecf01_parse_valor_sap(acc.get("valor"))
        if parsed is not None:
            v_out: Any = int(parsed) if parsed == int(parsed) else parsed
        else:
            vr = acc.get("valor")
            v_out = vr if vr is None or isinstance(vr, (int, float)) else str(vr)
        txt_linha = ""
        for tk in ("txt_acc", "TXT_ACC", "txt", "TXT", "Txt"):
            if tk in acc and acc.get(tk) is not None:
                txt_linha = str(acc.get(tk)).strip()
                break
        out.append(
            {
                "racct": str(acc.get("racct", "") if acc.get("racct") is not None else "").strip(),
                "txt_acc": txt_linha,
                "valor": v_out,
            }
        )
    return out


def _zf_ecf01_campos_extras_no(raw: Dict[str, Any]) -> Dict[str, Any]:
    ex: Dict[str, Any] = {}
    st = _zf_ecf01_ler_stufe(raw)
    if st is not None:
        ex["stufe"] = st
    acc = _zf_ecf01_normalizar_accounts_list(raw.get("accounts"))
    if acc:
        ex["accounts"] = acc
    return ex


def _zf_ecf01_parse_valor_sap(val: Any) -> Optional[float]:
    """
    Converte valor numérico SAP / JSON para float.
    Aceita: número; string com vírgula decimal e ponto milhar (ex.: 150.037.234,87);
    sinal negativo com menos à direita (ex.: 121.936.748,93-).
    """
    if val is None:
        return None
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return None
    neg = False
    if s.endswith("-"):
        neg = True
        s = s[:-1].strip()
    s = s.replace(" ", "")
    if not s:
        return None
    if "," in s:
        # Formato BR: 1.234.567,89
        s = s.replace(".", "").replace(",", ".")
    else:
        parts = s.split(".")
        if len(parts) > 1:
            last = parts[-1]
            if len(last) == 3 and len(parts) >= 2 and all(p.isdigit() for p in parts):
                s = "".join(parts)
            elif len(parts) > 2:
                s = "".join(parts[:-1]) + "." + parts[-1] if last.isdigit() else "".join(parts)
    try:
        x = float(s)
        return -x if neg else x
    except ValueError:
        return None


def _zf_ecf01_parent_id_vazio(pid: Any) -> bool:
    if pid is None:
        return True
    if isinstance(pid, str) and not pid.strip():
        return True
    return False


def _zf_ecf01_ler_parent_id(item: Dict[str, Any]) -> Any:
    for k in ("parent_id", "PARENT_ID", "ParentId", "parentId"):
        if k in item:
            return item.get(k)
    return None


def _zf_ecf01_dict_tem_chave_parent_id(d: Dict[str, Any]) -> bool:
    return any(k in d for k in ("parent_id", "PARENT_ID", "ParentId", "parentId"))


def _zf_ecf01_lista_parece_plana_com_parent_id(itens: List[Any]) -> bool:
    """Lista plana se algum objeto declara campo parent_id (mesmo que null nas raízes)."""
    for x in itens:
        if isinstance(x, dict) and _zf_ecf01_dict_tem_chave_parent_id(x):
            return True
    return False


def _zf_ecf01_raiz_tem_children_com_nos(itens: List[Any]) -> bool:
    """
    Verdadeiro se algum item raiz traz ``children`` com pelo menos um objeto (árvore recursiva
    ABAP ``lcl_balance_tree``). Nesse caso não se deve usar o montador de lista plana por
    ``parent_id``, mesmo que ``parent_id`` exista como campo espúrio.
    """
    for x in itens:
        if not isinstance(x, dict):
            continue
        ch = x.get("children")
        if isinstance(ch, list) and any(isinstance(c, dict) for c in ch):
            return True
    return False


def _zf_ecf01_indice_pai_por_id(itens: List[Dict[str, Any]], parent_id: str, filho_idx: int) -> int:
    """Primeiro índice cujo ``id`` coincide com ``parent_id`` (exceto o próprio filho)."""
    pid = (parent_id or "").strip()
    if not pid:
        return -1
    for j, it in enumerate(itens):
        if j == filho_idx:
            continue
        sid = str(it.get("id", "") if it.get("id") is not None else "").strip()
        if sid == pid:
            return j
    return -1


def _zf_ecf01_lista_plana_para_arvore(
    itens: List[Dict[str, Any]],
    agregar_somar_valor_proprio: bool = False,
) -> List[Dict[str, Any]]:
    """
    Monta raízes e filhos com parent_id == id (ordem da lista preservada nos arrays children).
    Raiz: parent_id vazio/null. Cada nó tem sempre ``children`` (lista, possivelmente vazia).

    Agregação: com filhos, ``valor`` do pai passa a ser a soma dos valores dos filhos (após
    agregação recursiva), ou soma + valor próprio se ``agregar_somar_valor_proprio`` for True.
    Folhas sem filhos mantêm o valor vindo do SAP.
    """
    rows: List[Dict[str, Any]] = [x for x in itens if isinstance(x, dict)]
    if not rows:
        return []

    nos: List[Dict[str, Any]] = []
    for raw in rows:
        v0 = _zf_ecf01_parse_valor_sap(raw.get("valor"))
        no: Dict[str, Any] = {
            "id": str(raw.get("id", "") if raw.get("id") is not None else ""),
            "conta": _zf_ecf01_ler_conta(raw),
            "text": _zf_ecf01_ler_texto_no(raw),
            "valor": v0,
            "children": [],
        }
        no.update(_zf_ecf01_campos_extras_no(raw))
        nos.append(no)

    raizes: List[Dict[str, Any]] = []
    for i, raw in enumerate(rows):
        pid = _zf_ecf01_ler_parent_id(raw)
        if _zf_ecf01_parent_id_vazio(pid):
            raizes.append(nos[i])
            continue
        pidx = _zf_ecf01_indice_pai_por_id(rows, str(pid).strip(), filho_idx=i)
        if pidx >= 0:
            nos[pidx]["children"].append(nos[i])
        else:
            raizes.append(nos[i])

    def agregar(no: Dict[str, Any]) -> float:
        ch = no.get("children") or []
        if not ch:
            v = no.get("valor")
            f = float(v) if v is not None else 0.0
            no["valor"] = int(f) if f == int(f) else f
            return f
        s = sum(agregar(c) for c in ch)
        proprio = _zf_ecf01_parse_valor_sap(no.get("valor"))
        base = float(proprio) if proprio is not None else 0.0
        total = base + s if agregar_somar_valor_proprio else s
        no["valor"] = int(total) if total == int(total) else total
        return float(total)

    for r in raizes:
        agregar(r)
    return raizes


def _zf_ecf01_buscar_chave_dict(d: Dict[str, Any], *nomes: str) -> Any:
    for nome in nomes:
        if nome in d:
            return d[nome]
    lower_map = {str(k).upper(): k for k in d}
    for nome in nomes:
        k = lower_map.get(nome.upper())
        if k is not None:
            return d[k]
    return None


def _zf_ecf01_extrair_r_return(result: Optional[Dict[str, Any]]) -> str:
    """Somente R_RETURN (string); o balanço vem como JSON dentro deste campo."""
    if not result or not isinstance(result, dict):
        return ""
    r_ret = _zf_ecf01_buscar_chave_dict(result, "R_RETURN", "E_RETURN", "EV_RETURN")
    if r_ret is None:
        return ""
    return str(r_ret).strip()


def _zf_ecf01_normalizar_no_arvore(no: Any) -> Dict[str, Any]:
    if not isinstance(no, dict):
        return {"id": "", "conta": "", "text": "", "valor": None, "children": []}
    ch_raw = no.get("children")
    children_in = ch_raw if isinstance(ch_raw, list) else []
    parsed = _zf_ecf01_parse_valor_sap(no.get("valor"))
    if parsed is not None:
        valor_out: Any = int(parsed) if parsed == int(parsed) else parsed
    else:
        vraw = no.get("valor")
        valor_out = vraw if vraw is None or isinstance(vraw, (int, float)) else str(vraw)
    node: Dict[str, Any] = {
        "id": str(no.get("id", "") if no.get("id") is not None else ""),
        "conta": _zf_ecf01_ler_conta(no),
        "text": _zf_ecf01_ler_texto_no(no),
        "valor": valor_out,
        "children": [_zf_ecf01_normalizar_no_arvore(c) for c in children_in],
    }
    node.update(_zf_ecf01_campos_extras_no(no))
    return node


def _zf_ecf01_agregar_valores_arvore_aninhada(
    nos: List[Dict[str, Any]],
    agregar_somar_valor_proprio: bool = False,
) -> None:
    """Para árvore já aninhada: recalcula valor dos pais a partir dos filhos (pós-ordem)."""

    def agregar(no: Dict[str, Any]) -> float:
        ch = no.get("children") if isinstance(no.get("children"), list) else []
        if not ch:
            p = _zf_ecf01_parse_valor_sap(no.get("valor"))
            f = float(p) if p is not None else 0.0
            no["valor"] = int(f) if f == int(f) else f
            return f
        s = sum(agregar(c) for c in ch)
        proprio = _zf_ecf01_parse_valor_sap(no.get("valor"))
        base = float(proprio) if proprio is not None else 0.0
        total = base + s if agregar_somar_valor_proprio else s
        no["valor"] = int(total) if total == int(total) else total
        return float(total)

    for n in nos:
        agregar(n)


def _zf_ecf01_sanitizar_inteiros_zero_esquerda_json(s: str) -> str:
    """
    JSON não permite inteiros com zero à esquerda (ex.: ``04``, ``007``). O ABAP costuma formatar
    ``stufe`` assim; o ``json`` do Python falha com ``Expecting ',' delimiter`` na posição do segundo dígito.

    Só altera números após ``:`` (valor de campo), não texto entre aspas (ex.: ``"0011110001"``).
    """
    return re.sub(
        r'(:\s*)(-?)0+([1-9]\d*)(\.\d+)?(?=[\s,\]\}]|$)',
        lambda m: m.group(1) + (m.group(2) or "") + m.group(3) + (m.group(4) or ""),
        s,
    )


def _zf_ecf01_sanitizar_separadores_json_sap(s: str) -> str:
    """
    Corrige concatenação inválida comum em saída ABAP: objetos ou arrays colados sem vírgula.

    Ex.: ``[{...}{...}]`` ou ``{...}{...}`` — o parser JSON exige ``,`` entre valores; sem isso
    ocorre ``Expecting ',' delimiter``. Não altera o conteúdo dentro de strings (não há regex
    que percorra estado de string); se ``txt_balance`` contiver literal ``}{``, haverá falso
    positivo (caso raro).
    """
    t = re.sub(r"}\s*{", "},{", s)
    t = re.sub(r"]\s*\[", "],[", t)
    return t


# Padrões para inserir vírgula entre membros de um mesmo objeto quando o ABAP omite a vírgula
# (gera ``Expecting ',' delimiter`` em posição fixa, ex. após ``stufe`` / antes de ``accounts``).
_ZF_ECF01_RE_VIRGULA_STR_STR = re.compile(
    r'("(?:\\.|[^"\\])*")\s+("(?:\\.|[^"\\])*"\s*:)',
)
_ZF_ECF01_RE_VIRGULA_NUM_STR = re.compile(
    r"(-?\d+(?:\.\d+)?)\s+(" r'"(?:\\.|[^"\\])*"\s*:' r")",
)
_ZF_ECF01_RE_VIRGULA_BOOL_STR = re.compile(
    r"\b(true|false|null)\s+(" r'"(?:\\.|[^"\\])*"\s*:' r")",
    re.IGNORECASE,
)
_ZF_ECF01_RE_VIRGULA_FECHA_STR = re.compile(
    r"([\}\]])\s+(" r'"(?:\\.|[^"\\])*"\s*:' r")",
)


def _zf_ecf01_sanitizar_virgulas_membros_json(s: str) -> str:
    """
    Insere vírgulas omitidas entre pares ``valor`` / ``"próxima_chave":`` no mesmo objeto.

    Cobre casos como ``"stufe":1 "accounts":[]``, ``"x":"y" "z":1`` ou ``...} "k":`` sem vírgula
    antes de ``"k"``. Executa várias passadas até estabilizar (várias omissões seguidas).
    """
    t = s
    for _ in range(48):
        t0 = t
        t = _ZF_ECF01_RE_VIRGULA_STR_STR.sub(r"\1,\2", t)
        t = _ZF_ECF01_RE_VIRGULA_NUM_STR.sub(r"\1,\2", t)
        t = _ZF_ECF01_RE_VIRGULA_BOOL_STR.sub(r"\1,\2", t)
        t = _ZF_ECF01_RE_VIRGULA_FECHA_STR.sub(r"\1,\2", t)
        if t == t0:
            break
    return t


def _zf_ecf01_sanitizar_json_r_return_abap(s: str) -> str:
    """Pipeline: zeros à esquerda em inteiros + separadores ``}{`` / ``][`` + vírgulas entre membros."""
    t = _zf_ecf01_sanitizar_inteiros_zero_esquerda_json(s)
    for _ in range(8):
        t2 = _zf_ecf01_sanitizar_separadores_json_sap(t)
        t2 = _zf_ecf01_sanitizar_virgulas_membros_json(t2)
        t2 = _zf_ecf01_sanitizar_inteiros_zero_esquerda_json(t2)
        if t2 == t:
            return t
        t = t2
    return t


def _zf_ecf01_raw_decode_multiplos_valores(s: str) -> Tuple[Optional[Any], Optional[str]]:
    """Decodifica um ou mais valores JSON adjacentes (vírgulas / espaços entre eles)."""
    decoder = json.JSONDecoder()
    idx = 0
    n = len(s)
    valores: List[Any] = []
    try:
        while idx < n:
            while idx < n and s[idx] in " \t\n\r,":
                idx += 1
            if idx >= n:
                break
            obj, end = decoder.raw_decode(s, idx)
            valores.append(obj)
            idx = end
        while idx < n and s[idx] in " \t\n\r":
            idx += 1
        if idx < n:
            trecho = s[idx : idx + 48].replace("\n", " ")
            return None, f"Texto após JSON válido (posição {idx}): {trecho!r}"
    except json.JSONDecodeError as e:
        return None, str(e)

    if not valores:
        return None, "Nenhum JSON encontrado em R_RETURN."

    if len(valores) == 1:
        return valores[0], None
    return valores, None


def _zf_ecf01_contar_nos_arvore(nos: List[Dict[str, Any]]) -> int:
    t = 0
    for n in nos:
        t += 1
        ch = n.get("children")
        if isinstance(ch, list) and ch:
            t += _zf_ecf01_contar_nos_arvore(ch)
    return t


def _zf_ecf01_carregar_json_r_return(s: str) -> Tuple[Any, Optional[str]]:
    """
    Interpreta o texto de R_RETURN como JSON.

    Aceita um array ou um objeto único. Também aceita **vários objetos JSON concatenados**
    separados por vírgula e espaços (ex.: ``{...} , {...}``), que o SAP/ABAP costuma montar
    em vez de um único array — caso em que ``json.loads`` falha com "Extra data".

    Se o ABAP montar **objetos colados sem vírgula** (ex.: ``[{...}{...}]`` ou ``{...}{...}``),
    insere ``,`` entre ``}{`` / ``][``.

    Se omitir vírgula **entre campos do mesmo objeto** (ex.: ``"stufe":1 "accounts":[]``), aplica
    sanitização adicional (regex) antes de nova tentativa de parse.

    Inteiros com **zero à esquerda** (ex.: ``"stufe":04``), inválidos em JSON estrito, são normalizados
    (ex.: ``"stufe":4``).
    """
    s = (s or "").strip()
    if s.startswith("\ufeff"):
        s = s.lstrip("\ufeff").strip()
    if not s:
        return None, None

    s_led = _zf_ecf01_sanitizar_inteiros_zero_esquerda_json(s)
    s_san = _zf_ecf01_sanitizar_separadores_json_sap(s)
    s_full = _zf_ecf01_sanitizar_json_r_return_abap(s)
    candidatos: List[str] = []
    for cand in (s, s_led, s_san, s_full):
        if cand not in candidatos:
            candidatos.append(cand)

    primeiro_erro: Optional[str] = None
    for cand in candidatos:
        try:
            return json.loads(cand), None
        except json.JSONDecodeError as e:
            if primeiro_erro is None:
                primeiro_erro = str(e)

    ultimo_raw: Optional[str] = None
    for cand in candidatos:
        data, err_raw = _zf_ecf01_raw_decode_multiplos_valores(cand)
        if err_raw is None:
            return data, None
        ultimo_raw = err_raw

    msg = primeiro_erro or ultimo_raw or "JSON inválido em R_RETURN."
    mpos = re.search(r"\(char (\d+)\)", msg)
    if mpos:
        try:
            pos = int(mpos.group(1))
        except ValueError:
            pos = -1
        if 0 <= pos <= len(s):
            lo = max(0, pos - 40)
            hi = min(len(s), pos + 40)
            frag = s[lo:hi].replace("\n", " ").replace("\r", "")
            msg = f"{msg} | trecho em [{lo}:{hi}]: {frag!r}"
    return None, msg


def _zf_ecf01_parse_arvore_r_return(
    raw: str,
    agregar_somar_valor_proprio: bool = False,
    reagregar_arvore_aninhada: bool = False,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Interpreta o JSON em ``R_RETURN`` (ZF_ECF01 / balanço hierárquico).

    **Formato 1 — árvore recursiva (ex.: ``lcl_balance_tree``):** array de raízes; cada nó com
    ``id``, ``text``, ``valor``, ``accounts``[], ``children``[] (mesma forma recursiva). Contas:
    ``racct``, ``txt`` ou ``txt_acc``, ``valor``. Valores já vêm consolidados do SAP; por padrão
    não se recalcula o pai no Python.

    **Formato 2 — lista plana:** objetos com ``parent_id`` (e usualmente ``txt_balance``,
    ``stufe``) sem ``children`` preenchidos nas raízes; monta-se a árvore por ``parent_id``.

    **Saída normalizada:** ``id``, ``conta`` (= ``id`` da linha quando não há ``conta``), ``text``,
    ``valor``, ``children``, ``accounts`` com ``racct``, ``txt_acc`` (unificado a partir de ``txt``
    ou ``txt_acc``), opcionalmente ``stufe``.
    """
    s = (raw or "").strip()
    if not s:
        return [], None
    data, err_load = _zf_ecf01_carregar_json_r_return(s)
    if err_load:
        return [], f"R_RETURN não contém JSON válido: {err_load}"
    if data is None:
        return [], None
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return [], "R_RETURN JSON deve ser um array (ou um objeto) na raiz."
    if not data:
        return [], None

    if _zf_ecf01_lista_parece_plana_com_parent_id(data) and not _zf_ecf01_raiz_tem_children_com_nos(
        data
    ):
        planos = [x for x in data if isinstance(x, dict)]
        arvore = _zf_ecf01_lista_plana_para_arvore(planos, agregar_somar_valor_proprio=agregar_somar_valor_proprio)
        return arvore, None

    arvore = [_zf_ecf01_normalizar_no_arvore(n) for n in data]
    if reagregar_arvore_aninhada:
        _zf_ecf01_agregar_valores_arvore_aninhada(arvore, agregar_somar_valor_proprio=agregar_somar_valor_proprio)
    return arvore, None


def _zf_ecf01_bool_param(params: Dict[str, Any], *keys: str, default: bool = False) -> bool:
    for k in keys:
        if k in params and params[k] is not None:
            v = params[k]
            if isinstance(v, str):
                return v.strip().lower() in ("1", "true", "yes", "sim", "s")
            return bool(v)
    return default


def _zf_ecf01_montar_parametros(
    i_bukrs: str, i_month_b: int, i_month_v: int, i_year: int, i_ktopl: str, i_versn: str
) -> Dict[str, str]:
    """Parâmetros de importação ZF_ECF01: I_MONTH_B (inicial), I_MONTH_V (final), 2 dígitos."""
    return {
        "I_BUKRS": str(i_bukrs).strip(),
        "I_MONTH_B": f"{int(i_month_b):02d}",
        "I_MONTH_V": f"{int(i_month_v):02d}",
        "I_YEAR": str(int(i_year)),
        "I_KTOPL": str(i_ktopl).strip(),
        "I_VERSN": str(i_versn).strip(),
    }


def _zf_ecf01_resolver_intervalo_meses(
    params: Dict[str, Any],
) -> Tuple[Optional[Tuple[int, int, int]], Optional[str]]:
    """
    Resolve (ano, mês/período inicial, mês/período final) para uma única chamada RFC.

    Aceita i_month_b / i_month_v (ou I_MONTH_B / I_MONTH_V), ou i_month_ini / i_month_fim
    como alias; período único: i_month + i_year (define B = V = i_month).
    Números podem ultrapassar 12 (ex.: 1–16).
    """
    mb = params.get("i_month_b")
    if mb is None:
        mb = params.get("I_MONTH_B")
    mv = params.get("i_month_v")
    if mv is None:
        mv = params.get("I_MONTH_V")

    if mb is None and mv is None:
        mi = params.get("i_month_ini")
        if mi is None:
            mi = params.get("I_MONTH_INI")
        mf = params.get("i_month_fim")
        if mf is None:
            mf = params.get("I_MONTH_FIM")
        mb, mv = mi, mf

    if (mb is not None) ^ (mv is not None):
        return None, (
            "Informe ambos i_month_b e i_month_v (período inicial e final na RFC), "
            "ou i_month_ini e i_month_fim, ou i_month com i_year."
        )

    if mb is not None and mv is not None:
        y_raw = params.get("i_year")
        if y_raw is None:
            y_raw = params.get("I_YEAR")
        if y_raw is None:
            return None, "Informe i_year junto com o intervalo de períodos."
        try:
            y = int(y_raw)
            a, b = int(mb), int(mv)
        except (TypeError, ValueError):
            return None, "Ano ou número de período inválido."
        if y < 1900 or y > 9999:
            return None, "Ano fora do intervalo permitido."
        if a < 1 or a > _ZF_ECF01_MAX_NUMERO_PERIODO or b < 1 or b > _ZF_ECF01_MAX_NUMERO_PERIODO:
            return None, (
                f"Período deve estar entre 1 e {_ZF_ECF01_MAX_NUMERO_PERIODO} "
                "(valores enviados a I_MONTH_B e I_MONTH_V)."
            )
        if a > b:
            a, b = b, a
        qtd = b - a + 1
        if qtd > _ZF_ECF01_MAX_INTERVALO_PERIODOS:
            return None, (
                f"Intervalo excede {_ZF_ECF01_MAX_INTERVALO_PERIODOS} períodos. "
                "Reduza a diferença entre inicial e final."
            )
        return (y, a, b), None

    ms = params.get("i_month")
    if ms is None:
        ms = params.get("I_MONTH")
    if ms is not None:
        y_raw = params.get("i_year")
        if y_raw is None:
            y_raw = params.get("I_YEAR")
        if y_raw is None:
            return None, "Informe i_year junto com i_month."
        try:
            y = int(y_raw)
            m = int(ms)
        except (TypeError, ValueError):
            return None, "Período ou ano inválido."
        if m < 1 or m > _ZF_ECF01_MAX_NUMERO_PERIODO:
            return None, (
                f"i_month (período) deve estar entre 1 e {_ZF_ECF01_MAX_NUMERO_PERIODO}."
            )
        if y < 1900 or y > 9999:
            return None, "Ano fora do intervalo permitido."
        return (y, m, m), None

    return None, (
        "Informe i_month_b e i_month_v (ou i_month_ini e i_month_fim) e i_year, ou i_month e i_year."
    )


def _get_sap_connection_model():
    from app.db_GDF.Public.models import ConexaoSap
    return ConexaoSap


class SapRfc:
    """
    Classe responsável pela comunicação com SAP via RFC usando registros da tabela SapConnection.
    A conexão é sempre vinculada ao cliente: use cod_cliente para buscar o registro em SapConnection.

    Padrão para novas funcionalidades RFC:
      - Criar um método com nome da funcionalidade.
      - Chamar SapRfc.call(cod_cliente, nome_rfc, **params) [abre conexão, chama RFC, fecha].
      - Ou SapRfc.with_connection(cod_cliente, lambda sap: sap.call(...)) para várias chamadas.
    """
    _last_connect_error = ""

    # -------------------------------------------------------------------------
    # Conexão e chamada genérica (use estes dentro dos métodos de funcionalidade)
    # -------------------------------------------------------------------------

    @staticmethod
    def is_available():
        """Retorna True se o PyRFC está instalado."""
        return PYRFC_AVAILABLE

    @staticmethod
    def pyrfc_mensagem_indisponivel() -> str:
        """
        Mensagem para API/UI quando o PyRFC não carrega (pacote ausente, SDK ou LD_LIBRARY_PATH).
        """
        det_full = (PYRFC_IMPORT_ERROR or "").strip()
        det = det_full[:240] + ("..." if len(det_full) > 240 else "") if det_full else ""

        # Pacote Python não instalado no mesmo interpretador do Gunicorn/Streamlit/Celery
        if "no module named" in det_full.lower() and "pyrfc" in det_full.lower():
            return (
                "Integração SAP inativa: o pacote Python **pyrfc** não está instalado neste ambiente. "
                "Ative o mesmo venv do servidor (ex.: GDF_PJT/venv) e execute: `pip install pyrfc`. "
                "Em seguida instale o SAP NetWeaver RFC SDK em `<raiz-do-repositório>/nwrfcsdk`, "
                "configure SAPNWRFC_HOME e LD_LIBRARY_PATH (nwrfcsdk/lib) e reinicie os processos."
                + (f" (detalhe: {det})" if det else "")
            )

        # SDK / biblioteca nativa ausente ou loader não encontra libsapnwrfc.so
        if any(
            x in det_full.lower()
            for x in (
                "libsapnwrfc",
                "cannot open shared object",
                "connection",
                "importerror",
                "_cyrfc",
            )
        ):
            msg = (
                "Integração SAP inativa: o PyRFC não carregou a biblioteca nativa do SAP. "
                "Instale o SAP NetWeaver RFC SDK, coloque em `<raiz-do-repositório>/nwrfcsdk` "
                "(com `lib/libsapnwrfc.so`), defina SAPNWRFC_HOME e inclua `nwrfcsdk/lib` em "
                "LD_LIBRARY_PATH antes de subir Django ou Streamlit, e reinicie."
            )
            return f"{msg} (detalhe: {det})" if det else msg

        msg = (
            "Integração SAP inativa: falha ao importar o PyRFC. "
            "1) No venv do projeto: `pip install pyrfc`. "
            "2) Instale o SAP NW RFC SDK em `nwrfcsdk`, com SAPNWRFC_HOME e LD_LIBRARY_PATH. "
            "3) Reinicie Django/Streamlit."
        )
        return f"{msg} (detalhe: {det})" if det else msg

    @staticmethod
    def get_connection(cod_cliente):
        """
        Retorna a primeira conexão SAP ativa para o cliente, ou None.
        Parâmetro obrigatório: cod_cliente (código do cliente para filtrar na tabela SapConnection).
        """
        if not cod_cliente:
            print("[SapRfc] get_connection: cod_cliente vazio, retornando None")
            return None
        SapConnection = _get_sap_connection_model()
        conn = SapConnection.objects.filter(gdfcliente_id=cod_cliente, active=True).first()
        if conn:
            print(f"[SapRfc] get_connection: conexão encontrada para cliente '{cod_cliente}' (id={conn.id}, ashost={getattr(conn, 'ashost', '?')})")
        else:
            print(f"[SapRfc] get_connection: nenhuma conexão SAP ativa para cliente '{cod_cliente}'")
        return conn

    @staticmethod
    def get_active_connections(cod_cliente=None, queryset=None):
        """
        Retorna lista de conexões SAP ativas.
        - cod_cliente: se informado, filtra apenas conexões desse cliente (tabela SapConnection).
        - queryset: se informado, usa esse queryset (ignora cod_cliente).
        """
        SapConnection = _get_sap_connection_model()
        if queryset is not None:
            return list(queryset)
        qs = SapConnection.objects.filter(active=True)
        if cod_cliente:
            qs = qs.filter(gdfcliente_id=cod_cliente)
        return list(qs)

    @staticmethod
    def config_from_connection(conn):
        """
        Monta o dicionário de configuração para o pyrfc a partir de um registro SapConnection.
        """
        return {
            "ashost": conn.ashost or "",
            "sysnr": conn.sysnr or "",
            "client": conn.client or "",
            "user": conn.username or "",
            "passwd": conn.passwd or "",
            "lang": conn.lang or "",
            "decimal_output_as_string": "True",
        }

    @staticmethod
    def connect(conn):
        """
        Cria e retorna uma conexão pyrfc (Connection) para o registro SapConnection dado.
        Retorna None se PyRFC não estiver disponível ou se a conexão falhar.
        """
        if not PYRFC_AVAILABLE:
            print("[SapRfc] connect: PyRFC não disponível")
            return None
        config = SapRfc.config_from_connection(conn)
        print(f"[SapRfc] connect: abrindo conexão SAP (conn id={getattr(conn, 'id', '?')}, ashost={config.get('ashost', '')})")
        try:
            sap = PyRfcConnection(**config)
            print(f"[SapRfc] connect: conexão SAP aberta com sucesso (conn id={getattr(conn, 'id', '?')})")
            return sap
        except Exception as e:
            err_msg = str(e)
            SapRfc._last_connect_error = err_msg
            print(f"[SapRfc] connect: ERRO ao conectar SAP (conn id={getattr(conn, 'id', conn)}): {e}")
            return None

    @staticmethod
    def _mensagem_erro_com_vpn(erro: str) -> str:
        """
        Enriquece mensagem de erro com dica de VPN quando parecer falha de conectividade.
        A conexão RFC é feita pelo SERVIDOR (Django), não pelo navegador.
        """
        if not erro:
            return erro
        erro_lower = str(erro).lower()
        indicadores_rede = (
            'connection refused', 'connection timed out', 'timeout', 'host unreachable',
            'no route to host', 'network is unreachable', 'connection reset',
            'errno 111', 'errno 110', 'errno 113', 'errno 101',
        )
        if any(ind in erro_lower for ind in indicadores_rede):
            return (
                f"{erro} "
                "Se o SAP exige VPN, o servidor onde o Django roda deve estar conectado à VPN corporativa."
            )
        return erro

    @staticmethod
    def _resolve_conn(cod_cliente_or_conn):
        """Retorna SapConnection a partir de cod_cliente (str) ou do próprio registro (conn)."""
        if cod_cliente_or_conn is None:
            return None
        if isinstance(cod_cliente_or_conn, str):
            return SapRfc.get_connection(cod_cliente_or_conn)
        return cod_cliente_or_conn

    @staticmethod
    def call(cod_cliente_or_conn, rfc_name, **params):
        """
        Método responsável pela conexão: abre, chama o RFC e fecha.
        Use este método dentro de cada método de funcionalidade (um por RFC).

        Fluxo: 1) obtém conexão (por cod_cliente na SapConnection)
               2) chama a função RFC com **params
               3) fecha a comunicação

        Args:
            cod_cliente_or_conn: cod_cliente (str) para buscar conexão do cliente, ou
                                instância de SapConnection (model) se já tiver o registro
            rfc_name: nome do módulo de função RFC (ex: '/BRGMN/CUSTR_IMP_CUSTO')
            **params: parâmetros nomeados da chamada RFC (ex: I_V_BUKRS=..., I_V_BRANCH=...)

        Returns:
            tuple (success: bool, result_or_error)
        """
        if not PYRFC_AVAILABLE:
            print("[SapRfc] call: PyRFC não disponível")
            return False, SapRfc.pyrfc_mensagem_indisponivel()
        conn = SapRfc._resolve_conn(cod_cliente_or_conn)
        if conn is None:
            cod = cod_cliente_or_conn if isinstance(cod_cliente_or_conn, str) else getattr(cod_cliente_or_conn, 'gdfcliente_id', '?')
            print(f"[SapRfc] call: nenhuma conexão para cliente '{cod}'")
            return False, f"Nenhuma conexão SAP ativa para o cliente '{cod}' (tabela SapConnection)."
        sap = None
        try:
            print(f"[SapRfc] call: chamando RFC '{rfc_name}' (params keys: {list(params.keys())})")
            sap = SapRfc.connect(conn)
            if sap is None:
                print("[SapRfc] call: falha ao abrir conexão SAP")
                err = getattr(SapRfc, '_last_connect_error', '') or "Falha ao abrir conexão SAP."
                return False, SapRfc._mensagem_erro_com_vpn(err)
            result = sap.call(rfc_name, **params)
            print(f"[SapRfc] call: RFC '{rfc_name}' executado com sucesso (result type={type(result).__name__})")
            return True, result
        except Exception as e:
            print(f"[SapRfc] call: EXCEÇÃO ao chamar RFC '{rfc_name}': {e}")
            return False, SapRfc._mensagem_erro_com_vpn(str(e))
        finally:
            if sap is not None:
                try:
                    sap.close()
                    print("[SapRfc] call: conexão SAP fechada")
                except Exception as ex:
                    print(f"[SapRfc] call: aviso ao fechar conexão: {ex}")

    @staticmethod
    def with_connection(cod_cliente_or_conn, callback, close=True):
        """
        Abre uma conexão SAP (por cod_cliente ou registro SapConnection) e chama callback(sap).
        Útil para várias chamadas RFC na mesma conexão.

        Args:
            cod_cliente_or_conn: cod_cliente (str) ou instância de SapConnection (model)
            callback: função que recebe (sap) e retorna o que quiser
            close: se True, fecha a conexão ao final

        Returns:
            tuple (success: bool, result_or_error)
        """
        if not PYRFC_AVAILABLE:
            print("[SapRfc] with_connection: PyRFC não disponível")
            return False, SapRfc.pyrfc_mensagem_indisponivel()
        conn = SapRfc._resolve_conn(cod_cliente_or_conn)
        if conn is None:
            cod = cod_cliente_or_conn if isinstance(cod_cliente_or_conn, str) else getattr(cod_cliente_or_conn, 'gdfcliente_id', '?')
            print(f"[SapRfc] with_connection: nenhuma conexão para cliente '{cod}'")
            return False, f"Nenhuma conexão SAP ativa para o cliente '{cod}' (tabela SapConnection)."
        sap = None
        try:
            print("[SapRfc] with_connection: abrindo conexão para callback")
            sap = SapRfc.connect(conn)
            if sap is None:
                print("[SapRfc] with_connection: falha ao abrir conexão")
                return False, "Falha ao abrir conexão SAP."
            result = callback(sap)
            print("[SapRfc] with_connection: callback executado com sucesso")
            return True, result
        except Exception as e:
            print(f"[SapRfc] with_connection: EXCEÇÃO no callback: {e}")
            return False, str(e)
        finally:
            if close and sap is not None:
                try:
                    sap.close()
                    print("[SapRfc] with_connection: conexão fechada")
                except Exception as ex:
                    print(f"[SapRfc] with_connection: aviso ao fechar: {ex}")

    @staticmethod
    def run_for_active_connections(rfc_name, cod_cliente=None, params_callback=None, call_callback=None):
        """
        Itera sobre conexões SapConnection ativas e, para cada uma, abre conexão e chama o RFC.
        A conexão é por cliente: use cod_cliente para processar apenas esse cliente.

        Args:
            rfc_name: nome do RFC (ex: '/BRGMN/CUSTR_IMP_CUSTO')
            cod_cliente: opcional. Se informado, usa apenas conexões desse cliente (tabela SapConnection).
            params_callback: opcional. (conn) -> iterável de parâmetros.
            call_callback: opcional. (sap, conn) -> resultado.

        Exemplo:
            for conn, result in SapRfc.run_for_active_connections(
                '/BRGMN/CUSTR_IMP_CUSTO', cod_cliente='CLI01', params_callback=params_por_conexao
            ):
                print(conn, result)
        """
        if not PYRFC_AVAILABLE:
            print("❌ PyRFC não disponível. SAP desativado.")
            return
        conn_list = SapRfc.get_active_connections(cod_cliente=cod_cliente)
        if not conn_list:
            print(f"⚠️ Nenhuma conexão SAP ativa para o cliente '{cod_cliente or '(todos)'}'.")
            return
        for conn in conn_list:
            if call_callback:
                success, result = SapRfc.with_connection(conn, lambda sap: call_callback(sap, conn))
                if not success:
                    print(f"⚠️ Conexão {conn} (id={conn.id}): {result}")
                continue
            params_iter = params_callback(conn) if params_callback else None
            if params_iter is None:
                continue
            sap = SapRfc.connect(conn)
            if sap is None:
                print(f"⚠️ Nenhuma conexão aberta para {conn} (id={conn.id}).")
                continue
            try:
                for param_set in params_iter:
                    try:
                        if isinstance(param_set, dict):
                            result = sap.call(rfc_name, **param_set)
                        else:
                            result = sap.call(rfc_name, *param_set)
                        if result is not None:
                            yield (conn, result)
                    except Exception as e:
                        print(f"⚠️ Erro ao chamar {rfc_name} na conexão {conn.id}: {e}")
            finally:
                try:
                    sap.close()
                except Exception:
                    pass

    # -------------------------------------------------------------------------
    # Métodos de funcionalidade: um método por RFC (conexão → chamada → fechar)
    # -------------------------------------------------------------------------

    @staticmethod
    def importar_custo_cliente(cod_cliente, bukrs, branch, psdat_ini, psdat_fim):
        """
        Exemplo de método por funcionalidade:
          1. Chama o responsável pela conexão (SapRfc.call obtém conexão por cod_cliente).
          2. Chama a função RFC com os parâmetros.
          3. A comunicação é fechada ao final (SapRfc.call já faz isso).

        Returns:
            tuple (success: bool, result_or_error)
        """
        print(f"[SapRfc] importar_custo_cliente: cod_cliente={cod_cliente!r} bukrs={bukrs} branch={branch} psdat_ini={psdat_ini} psdat_fim={psdat_fim}")
        ok, res = SapRfc.call(
            cod_cliente,
            '/PRCIT/GDF_condicoes_pagamento',
            I_V_BUKRS=bukrs,
            I_V_BRANCH=branch,
            I_V_PSDAT_INI=psdat_ini,
            I_V_PSDAT_FIM=psdat_fim,
        )
        print(f"[SapRfc] importar_custo_cliente: resultado success={ok} result_type={type(res).__name__}")
        return ok, res

    @staticmethod
    def importar_relatorio_custo(cod_cliente, bukrs, branch, psdat_ini, psdat_fim, empresa=None, filial=None, persistir=True):
        """
        Chama a RFC /BRGMN/CUSTR_IMP_CUSTO para importar dados de custo do SAP e,
        se persistir=True, grava na tabela sap.relatorio_custo (RelatorioCusto),
        vinculando à Empresa e Filial do GDF.

        Args:
            cod_cliente: Código do cliente GDF (para conexão SAP).
            bukrs: Código da empresa no SAP (string ou objeto com atributo .bukrs).
            branch: Filial/ramo no SAP (string).
            psdat_ini: Data inicial do período (string ou date, formato aceito pelo SAP).
            psdat_fim: Data final do período (string ou date).
            empresa: Opcional. Instância de Empresa (GDF) para vincular aos registros.
                     Se None, tenta resolver por cod_empresa=bukrs.
            filial: Opcional. Instância de Filial (GDF) para vincular.
                    Se None e empresa informada, tenta Filial com cod_filial=branch.
            persistir: Se True, grava o retorno da RFC na tabela sap.relatorio_custo.

        Returns:
            dict: {
                'sucesso': bool,
                'mensagem': str,
                'total_linhas': int (linhas retornadas pela RFC),
                'total_gravados': int (registros inseridos/atualizados, se persistir=True),
                'resultado_rfc': result bruto da RFC (se sucesso),
            }
        """
        from decimal import Decimal, InvalidOperation
        from datetime import datetime
        from app.db_GDF.Public.models import Empresa, Filial
        from app.db_GDF.Sap.models import RelatorioCusto

        # Normalizar bukrs (aceitar objeto com .bukrs ou string)
        _bukrs = getattr(bukrs, 'bukrs', bukrs)
        if _bukrs is None:
            _bukrs = ''
        _bukrs = str(_bukrs).strip()

        print(f"[SapRfc] importar_relatorio_custo: cod_cliente={cod_cliente!r} bukrs={_bukrs} branch={branch} psdat_ini={psdat_ini} psdat_fim={psdat_fim} persistir={persistir}")

        if not SapRfc.is_available():
            return {
                'sucesso': False,
                'mensagem': SapRfc.pyrfc_mensagem_indisponivel(),
                'total_linhas': 0,
                'total_gravados': 0,
                'resultado_rfc': None,
            }

        ok, result = SapRfc.call(
            cod_cliente,
            "/BRGMN/CUSTR_IMP_CUSTO",
            I_V_BUKRS=_bukrs,
            I_V_BRANCH=branch or '',
            I_V_PSDAT_INI=psdat_ini,
            I_V_PSDAT_FIM=psdat_fim,
        )

        if not ok:
            return {
                'sucesso': False,
                'mensagem': result or 'Erro ao chamar RFC /BRGMN/CUSTR_IMP_CUSTO.',
                'total_linhas': 0,
                'total_gravados': 0,
                'resultado_rfc': None,
            }

        # Tabela de retorno da RFC /BRGMN/CUSTR_IMP_CUSTO
        table_data = result.get("T_RELAT003", []) if result and isinstance(result, dict) else []
        linhas = table_data if isinstance(table_data, list) else (list(table_data) if table_data else [])

        total_linhas = len(linhas)
        print(f"[SapRfc] importar_relatorio_custo: RFC retornou {total_linhas} linha(s)")

        if not persistir or total_linhas == 0:
            return {
                'sucesso': True,
                'mensagem': f'RFC executada. {total_linhas} linha(s) retornada(s).',
                'total_linhas': total_linhas,
                'total_gravados': 0,
                'resultado_rfc': result,
            }

        # Resolver Empresa e Filial para vincular
        if empresa is None and _bukrs:
            empresa = Empresa.objects.filter(cod_empresa=_bukrs).first()
        if filial is None and empresa and branch:
            filial = Filial.objects.filter(empresa=empresa, cod_filial=str(branch).strip()).first()

        # Mapeamento: nome da coluna no retorno SAP (uppercase) -> campo do modelo RelatorioCusto
        MAPEAMENTO_SAP = {
            'DOCNUM': 'docnum', 'MJAHR': 'mjahr', 'MBLNR': 'mblnr', 'MATNR': 'matnr', 'NFENUM': 'nfenum',
            'SERIES': 'series', 'DOCSTA': 'docsta', 'KUNNR': 'kunnr', 'NAME1': 'name1', 'ORT01': 'ort01',
            'CHAVE_ACESSO': 'chave_acesso', 'ITMNUM': 'itmnum', 'PSTDAT': 'pstdat', 'WERKS': 'werks',
            'NAME': 'name', 'STCD1': 'stcd1', 'UF_ORIGEM': 'uf_origem', 'UF_DESTINO': 'uf_destino',
            'CANCEL': 'cancel', 'MAKTX': 'maktx', 'MTART': 'mtart', 'MATKL': 'matkl', 'WGBEZ': 'wgbez',
            'CFOP': 'cfop', 'QTD_PROD': 'qtd_prod', 'UNID_MEDIDA': 'unid_medida', 'MEINS': 'meins',
            'UMREZ': 'umrez', 'MENGE_UMB': 'menge_umb', 'PRC_UNITARIO': 'prc_unitario',
            'PRC_UNIT_CST_LIQ': 'prc_unit_cst_liq', 'PRC_UNIT_CST_ADM': 'prc_unit_cst_adm',
            'BC_ICMS': 'bc_icms', 'PCT_ICMS': 'pct_icms', 'VLR_ICMS': 'vlr_icms',
            'BC_ICMS_ST': 'bc_icms_st', 'ALQ_ST': 'alq_st', 'VLR_ST': 'vlr_st',
            'BC_IPI': 'bc_ipi', 'PCT_IPI': 'pct_ipi', 'VLR_IPI': 'vlr_ipi',
            'BC_PIS': 'bc_pis', 'PCT_PIS': 'pct_pis', 'VLR_PIS': 'vlr_pis',
            'BC_COF': 'bc_cof', 'PCT_COF': 'pct_cof', 'VLR_COF': 'vlr_cof',
            'TP_DOC': 'tp_doc', 'TOTAL_IMPOSTOS': 'total_impostos', 'VLR_DESCONTO': 'vlr_desconto',
            'VLR_FRETE': 'vlr_frete', 'VLR_LIQUIDO': 'vlr_liquido', 'VLR_TOT_DOC': 'vlr_tot_doc',
            'CMV': 'cmv', 'LUCRO_0': 'lucro_0', 'MARGEM_0': 'margem_0', 'MARGEM_CONTRIB': 'margem_contrib',
            'CMV_GERENCIAL': 'cmv_gerencial', 'LUCRO_0_GERENCIAL': 'lucro_0_gerencial',
            'MARGEM_REAL': 'margem_real', 'LUCRO_REAL': 'lucro_real', 'MARGEM_CONTRIB_GER': 'margem_contrib_ger',
            'CMV_MEDIA': 'cmv_media', 'PER_TAXA_ADM': 'per_taxa_adm', 'VLR_TAXA_ADM': 'vlr_taxa_adm',
            'PER_TAXA_FRT': 'per_taxa_frt', 'VLR_TAXA_FRT': 'vlr_taxa_frt', 'CMV_UE': 'cmv_ue',
        }

        def _to_decimal(val):
            if val is None or val == '':
                return None
            if isinstance(val, Decimal):
                return val
            try:
                return Decimal(str(val).replace(',', '.'))
            except (InvalidOperation, TypeError):
                return None

        def _to_date(val):
            if val is None or val == '':
                return None
            if hasattr(val, 'date'):
                return val.date() if hasattr(val, 'date') else val
            if isinstance(val, str):
                for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
                    try:
                        return datetime.strptime(val[:10], fmt).date()
                    except (ValueError, TypeError):
                        continue
            return None

        gravados = 0
        for row in linhas:
            if not isinstance(row, dict):
                row = dict(row) if hasattr(row, 'keys') else {}
            row_upper = {str(k).strip().upper(): v for k, v in row.items()}
            kwargs = {'empresa': empresa, 'filial': filial}
            for sap_key, model_field in MAPEAMENTO_SAP.items():
                val = row_upper.get(sap_key) or row_upper.get(model_field.upper())
                if val is None:
                    continue
                if model_field == 'pstdat':
                    kwargs[model_field] = _to_date(val)
                elif model_field in (
                    'qtd_prod', 'umrez', 'menge_umb', 'prc_unitario', 'prc_unit_cst_liq', 'prc_unit_cst_adm',
                    'bc_icms', 'pct_icms', 'vlr_icms', 'bc_icms_st', 'alq_st', 'vlr_st',
                    'bc_ipi', 'pct_ipi', 'vlr_ipi', 'bc_pis', 'pct_pis', 'vlr_pis', 'bc_cof', 'pct_cof', 'vlr_cof',
                    'total_impostos', 'vlr_desconto', 'vlr_frete', 'vlr_liquido', 'vlr_tot_doc',
                    'cmv', 'lucro_0', 'margem_0', 'margem_contrib', 'cmv_gerencial', 'lucro_0_gerencial',
                    'margem_real', 'lucro_real', 'margem_contrib_ger', 'cmv_media',
                    'per_taxa_adm', 'vlr_taxa_adm', 'per_taxa_frt', 'vlr_taxa_frt', 'cmv_ue',
                ):
                    kwargs[model_field] = _to_decimal(val)
                else:
                    kwargs[model_field] = str(val).strip()

            docnum = (kwargs.get('docnum') or '').strip()
            mjahr = (kwargs.get('mjahr') or '').strip() or None
            mblnr = (kwargs.get('mblnr') or '').strip() or None
            if not docnum:
                continue
            kwargs.setdefault('docsta', ' ')
            key_fields = ('empresa', 'docnum', 'mjahr', 'mblnr')
            defaults = {}
            for k, v in kwargs.items():
                if k in key_fields or v is None:
                    continue
                try:
                    f = RelatorioCusto._meta.get_field(k)
                    if hasattr(f, 'max_length') and f.max_length and isinstance(v, str) and len(v) > f.max_length:
                        v = v[: f.max_length]
                except Exception:
                    pass
                defaults[k] = v
            try:
                RelatorioCusto.objects.update_or_create(
                    empresa=empresa,
                    docnum=docnum,
                    mjahr=mjahr,
                    mblnr=mblnr,
                    defaults=defaults,
                )
                gravados += 1
            except Exception as e:
                print(f"[SapRfc] importar_relatorio_custo: erro ao gravar linha docnum={docnum}: {e}")

        print(f"[SapRfc] importar_relatorio_custo: {gravados} registro(s) gravado(s) em sap.relatorio_custo")
        return {
            'sucesso': True,
            'mensagem': f'RFC executada. {total_linhas} linha(s) retornada(s), {gravados} gravado(s) em sap.relatorio_custo.',
            'total_linhas': total_linhas,
            'total_gravados': gravados,
            'resultado_rfc': result,
        }

    @staticmethod
    def consultar_balanco_financeiro(cod_cliente, **params):
        """
        RFC ZF_ECF01 — balanço financeiro.

        O SAP devolve o resultado em ``R_RETURN`` (string) contendo JSON:

        - **Lista plana** com ``parent_id`` (vazio/null na raiz), sem ``children`` nas raízes:
          monta ``children`` por ``parent_id == id``; agrega ``valor`` do pai (ou + próprio se
          ``agregar_pai_soma_propria``).
        - **Árvore recursiva** (ex.: ``lcl_balance_tree``): ``id``, ``text``, ``valor``,
          ``accounts`` (``racct``, ``txt`` ou ``txt_acc``), ``children`` aninhados. Valores
          consolidados vêm do SAP; por padrão **não** se recalcula o pai
          (``reagregar_arvore_aninhada`` falso). Use ``reagregar_arvore_aninhada`` verdadeiro
          só se quiser sobrescrever pais com a soma dos filhos.

        Parâmetros RFC: i_bukrs, i_month_b, i_month_v, i_year, i_ktopl, i_versn.
        Opcionais: ``agregar_pai_soma_propria``, ``reagregar_arvore_aninhada`` (bool).

        Retorno: sucesso, mensagem, r_return, arvore, total_nos, t_balance (legado vazio),
        total_linhas, colunas, periodo, opcoes_arvore.
        """
        cols = list(ZF_ECF01_ARVORE_COLUNAS)

        def _fail(
            msg: str,
            r_ret: str = "",
            periodo: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            return {
                "sucesso": False,
                "mensagem": msg,
                "r_return": r_ret,
                "arvore": [],
                "total_nos": 0,
                "t_balance": [],
                "total_linhas": 0,
                "colunas": cols,
                "periodo": periodo or {},
                "opcoes_arvore": {},
            }

        i_bukrs = str(params.get("i_bukrs") or params.get("I_BUKRS") or "").strip()
        intervalo, err_intervalo = _zf_ecf01_resolver_intervalo_meses(params)
        if err_intervalo or not intervalo:
            return _fail(err_intervalo or "Não foi possível determinar o período.")
        ref_year, month_b, month_v = intervalo
        periodo = {"i_year": ref_year, "i_month_b": month_b, "i_month_v": month_v}
        i_ktopl = str(params.get("i_ktopl") or params.get("I_KTOPL") or "").strip()
        i_versn = str(params.get("i_versn") or params.get("I_VERSN") or "").strip()

        if not i_bukrs:
            return _fail("Empresa (I_BUKRS) é obrigatória.", periodo=periodo)
        if not i_ktopl or not i_versn:
            return _fail("Plano de contas (I_KTOPL) e versão (I_VERSN) são obrigatórios.", periodo=periodo)

        if not SapRfc.is_available():
            return _fail(SapRfc.pyrfc_mensagem_indisponivel(), periodo=periodo)

        rfc_params = _zf_ecf01_montar_parametros(
            i_bukrs, month_b, month_v, ref_year, i_ktopl, i_versn
        )
        print(
            f"[SapRfc] consultar_balanco_financeiro: cod_cliente={cod_cliente!r} "
            f"I_BUKRS={rfc_params['I_BUKRS']} I_MONTH_B={rfc_params['I_MONTH_B']} "
            f"I_MONTH_V={rfc_params['I_MONTH_V']} I_YEAR={rfc_params['I_YEAR']}"
        )
        ok, result = SapRfc.call(cod_cliente, _RFC_BALANCO_FINANCEIRO, **rfc_params)

        if not ok:
            err = str(result or f"Erro ao chamar RFC {_RFC_BALANCO_FINANCEIRO}.")
            return _fail(err, periodo=periodo)

        r_return = _zf_ecf01_extrair_r_return(result if isinstance(result, dict) else None)
        agregar_somar = _zf_ecf01_bool_param(
            params, "agregar_pai_soma_propria", "i_agregar_pai_soma_propria"
        )
        reagregar = _zf_ecf01_bool_param(
            params,
            "reagregar_arvore_aninhada",
            "i_reagregar_arvore_aninhada",
            default=False,
        )
        opcoes_arvore = {
            "agregar_pai_soma_propria": agregar_somar,
            "reagregar_arvore_aninhada": reagregar,
        }
        arvore, err_json = _zf_ecf01_parse_arvore_r_return(
            r_return,
            agregar_somar_valor_proprio=agregar_somar,
            reagregar_arvore_aninhada=reagregar,
        )
        if err_json:
            return _fail(err_json, r_ret=r_return, periodo=periodo)

        total_nos = _zf_ecf01_contar_nos_arvore(arvore)
        label_periodo = f"{ref_year}: I_MONTH_B={month_b} … I_MONTH_V={month_v}"
        if not arvore:
            msg_ok = (
                "RFC executada; R_RETURN vazio ou sem nós."
                if not (r_return or "").strip()
                else "RFC executada; nenhum nó na árvore JSON."
            )
        elif month_b == month_v:
            msg_ok = "Dados obtidos com sucesso."
        else:
            msg_ok = f"Dados obtidos com sucesso."

        print(f"[SapRfc] consultar_balanco_financeiro: {total_nos} nó(s) no JSON de R_RETURN")
        return {
            "sucesso": True,
            "mensagem": msg_ok,
            "r_return": r_return,
            "arvore": arvore,
            "total_nos": total_nos,
            "t_balance": [],
            "total_linhas": total_nos,
            "colunas": cols,
            "periodo": periodo,
            "opcoes_arvore": opcoes_arvore,
        }


def enviar_condicoes_pagamento_sap(id_lote, cod_cliente, condicoes_lista):
    """
    Envia as condições de pagamento ao SAP via RFC e retorna o que o SAP aplicou por chave.
    Usa cod_cliente (do lote/grupo) para obter a conexão SAP.

    Args:
        id_lote: ID do lote (reprocessamento).
        cod_cliente: Código do cliente GDF (para mapear conexão SAP).
        condicoes_lista: Lista de dict com chave_nfe, numero_nfe, serie_nfe,
                         condicao_pagamento_nfe, condicao_pagamento_sap (opcional).

    Returns:
        dict: {
            'sucesso': bool,
            'mensagem': str,
            'retornos': [ {'chave_nfe': str, 'condicao_sap': str}, ... ]
        }
    """
    print(f"[SapRfc] enviar_condicoes_pagamento_sap: INÍCIO id_lote={id_lote} cod_cliente={cod_cliente!r} qtd_condicoes={len(condicoes_lista) if condicoes_lista else 0}")

    if not condicoes_lista:
        print("[SapRfc] enviar_condicoes_pagamento_sap: lista vazia, retornando sucesso sem envio")
        return {'sucesso': True, 'mensagem': 'Nenhum registro para enviar.', 'retornos': []}

    if not SapRfc.is_available():
        print("[SapRfc] enviar_condicoes_pagamento_sap: PyRFC não disponível")
        retornos = [
            {'chave_nfe': (c.get('chave_nfe') or ''), 'condicao_sap': (c.get('condicao_pagamento_sap') or c.get('condicao_pagamento_nfe') or '-')}
            for c in condicoes_lista
        ]
        return {
            'sucesso': False,
            'mensagem': SapRfc.pyrfc_mensagem_indisponivel(),
            'retornos': retornos,
        }

    if not cod_cliente:
        print("[SapRfc] enviar_condicoes_pagamento_sap: cod_cliente não informado")
        retornos = [
            {'chave_nfe': (c.get('chave_nfe') or ''), 'condicao_sap': (c.get('condicao_pagamento_sap') or c.get('condicao_pagamento_nfe') or '-')}
            for c in condicoes_lista
        ]
        return {
            'sucesso': False,
            'mensagem': 'Cliente não informado. Não é possível obter conexão SAP.',
            'retornos': retornos,
        }

    # Mapear para estrutura ZGDF_S_COND_PAGAMENTO: CHAVE, COND_PAG_NFE, COND_PAG_SAP
    # (SAP retorna a mesma tabela com STATUS preenchido em R_T_COND)
    t_cond_pagamento = []
    for c in condicoes_lista:
        t_cond_pagamento.append({
            'CHAVE': (c.get('chave_nfe') or '')[:44],
            'COND_PAG_NFE': (c.get('condicao_pagamento_nfe') or '')[:50],
            'COND_PAG_SAP': (c.get('condicao_pagamento_sap') or '')[:4],
        })
    print(f"[SapRfc] enviar_condicoes_pagamento_sap: montada tabela T_COND_PAGAMENTO com {len(t_cond_pagamento)} registro(s), chamando RFC ZGDF_CONDICOES_PAGAMENTO")

    success, result = SapRfc.call(
        cod_cliente,
        'ZGDF_CONDICOES_PAGAMENTO',
        T_COND_PAGAMENTO=t_cond_pagamento,
    )

    # Status válidos do modelo CondicaoPagamentoLote: P, E, S, U, I, R
    STATUS_VALIDOS = ('P', 'E', 'S', 'U', 'I', 'R')

    retornos = [
        {
            'chave_nfe': (c.get('chave_nfe') or ''),
            'condicao_sap': (c.get('condicao_pagamento_sap') or c.get('condicao_pagamento_nfe') or '-'),
            'status': 'R',
        }
        for c in condicoes_lista
    ]
    if not success:
        print(f"[SapRfc] enviar_condicoes_pagamento_sap: FALHA na chamada RFC - {result}")
        return {
            'sucesso': False,
            'mensagem': result or 'Erro ao chamar SAP.',
            'retornos': retornos,
        }
    # SAP retorna R_T_COND (mesma tabela com STATUS: P, E, S, U, I, R)
    if result:
        r_t_cond = result.get('R_T_COND') or result.get('T_COND_PAGAMENTO') or []
        print(f"[SapRfc] enviar_condicoes_pagamento_sap: RFC retornou result com {len(r_t_cond)} item(ns) em R_T_COND/T_COND_PAGAMENTO")
        retornos = []
        for r in r_t_cond:
            status_sap = (r.get('STATUS') or r.get('status') or '').strip().upper()[:1]
            status_lote = status_sap if status_sap in STATUS_VALIDOS else 'S'
            retornos.append({
                'chave_nfe': (r.get('CHAVE') or r.get('chave') or ''),
                'condicao_sap': (r.get('COND_PAG_SAP') or r.get('cond_pag_sap') or ''),
                'status': status_lote,
            })
    else:
        print("[SapRfc] enviar_condicoes_pagamento_sap: RFC retornou result vazio/None, usando retornos padrão")
    print(f"[SapRfc] enviar_condicoes_pagamento_sap: SUCESSO - {len(retornos)} retorno(s)")
    return {
        'sucesso': True,
        'mensagem': f'{len(retornos)} registro(s) enviado(s) ao SAP.',
        'retornos': retornos,
    }
