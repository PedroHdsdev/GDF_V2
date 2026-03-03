# Subsoluções e a página "Produtos Process"

## O que existe no código hoje

**Não existe** nenhuma página ou URL chamada "Produtos Process" no projeto.

### Estrutura do menu (subsoluções)

O menu lateral vem da **sessão** (`t_solucoes`), montada no login a partir das tabelas:

- **solucoes** (ex.: Processamento Fiscal)
- **subsolucoes** (ex.: Pro_CargaXml, Pro_CargaSped, Pro_Relatorio)
- **subsolucoes_acesso** (quais grupos veem cada subsolução)

Fluxo quando você clica em um item do menu:

1. O link é: `/get_subsolucao/<cod_subsolucao>/` (ex.: `/get_subsolucao/Pro_CargaXml/`).
2. A view `fn_view_obter_subsolucao` recebe esse `cod_subsolucao` e faz:
   - `redirect(sub.get('cod_subsolucao'))`
3. Ou seja, o **redirect** usa o `cod_subsolucao` como **nome da rota** no Django (`name=` em `urls.py`).

As únicas subsoluções que têm rota definida no código são:

| cod_subsolucao  | Descrição   | URL (name)    | Página real        |
|-----------------|------------|---------------|--------------------|
| Pro_CargaXml    | Carga XML  | Pro_CargaXml  | /CargaXml/         |
| Pro_CargaSped   | Carga SPED | Pro_CargaSped | /CargaSped/        |
| Pro_Relatorio   | Relatório  | Pro_Relatorio | /Relatorio/        |

Se no **banco** existir uma subsolução com outro código (ex.: "Produtos Process" ou "Pro_Produtos"), o menu mostrará esse item, mas ao clicar o redirect tentará uma rota com esse mesmo nome. Como não há `path(..., name='Pro_Produtos')` (ou equivalente) em `urls.py`, o Django pode gerar erro ou levar a um 404.

---

## Onde "produtos" aparecem no sistema

"Produtos" no projeto são **dados**, não uma subsolução de menu:

1. **NFe – itens da nota**  
   Modelo `NFe_Produto` em `app/db_GDF/NFe/models.py`: produtos/serviços de cada NF-e (descrição, NCM, quantidade, valores, impostos).

2. **Carga XML**  
   Ao importar XML de NFe, a classe `CargaXml` preenche `NFe_Produto` (método `_processar_produtos`).

3. **Relatório Fiscal**  
   A API de relatório NFe (ex.: `/api/relatorio/nfe/<id>/`) devolve os itens da nota; no front podem ser exibidos como "produtos" daquela NFe.

4. **Dashboard Streamlit**  
   Os relatórios Streamlit usam `NFe_Produto` para gráficos (por produto, quantidade, etc.). Isso é uma aplicação separada (Streamlit), não uma página Django do menu.

Ou seja: não há uma **página** "Produtos" ou "Produtos Process" no Django; há apenas uso dos **dados** de produtos (NFe, relatório, Streamlit).

---

## Se você vê "Produtos Process" no menu

Isso indica que existe um registro na tabela **subsolucoes** (ou nome parecido) com descrição "Produtos Process" (ou "Produtos") para alguma solução (ex.: Processamento). Esse registro foi criado **fora** do que está nas migrations (por Admin ou script).

Para entender e corrigir:

1. **Conferir no banco**  
   - Tabela `subsolucoes`: veja as linhas com descrição tipo "Produtos" ou "Produtos Process" e anote o valor de `cod_subSolucoes` (ex.: `Pro_Produtos`).

2. **Duas opções**  
   - **Remover o item do menu**  
     Apagar ou desativar esse registro de subsolução (e, se existir, o acesso em `subsolucoes_acesso`) para esse grupo, para o item sumir do menu.  
   - **Criar a página de verdade**  
     - Em `urls.py`:  
       `path('ProdutosProcess/', views.fn_view_produtos_process, name='Pro_Produtos')`  
       (ou o mesmo `name` que está em `cod_subSolucoes`).  
     - Em `views.py`:  
       Criar `fn_view_produtos_process` que faz o que você quiser (ex.: listar produtos das NFe do cliente, filtros, etc.).  
     - Opcional: criar template em `templates/...` e retornar `render(request, '...', context)`.

---

## Resumo

- **"Produtos Process"** não é uma página implementada no código; no máximo é um **item de menu** vindo do banco (subsolução sem rota correspondente).
- **Produtos** no sistema = itens de NFe (`NFe_Produto`), usados em Carga XML, Relatório e Streamlit.
- Para "entender" essa "nova página": ou ela ainda não existe (só o item no menu) e você pode removê-la ou implementar a view + URL com o mesmo `name` do `cod_subsolucao`.

Se você disser se quer **só remover o item do menu** ou **criar a página de Produtos Process** (e o que ela deve mostrar), dá para detalhar o passo a passo (SQL/Admin + código).
