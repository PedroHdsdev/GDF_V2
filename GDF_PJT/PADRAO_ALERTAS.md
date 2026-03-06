# Padrão de exibição de erros e avisos – Painel GDF

Este documento define o padrão único para exibir **erros**, **avisos** e **mensagens de sucesso** em todo o painel (página, modal, formulários).

## Regras gerais

- **Não usar** `alert()` do navegador para mensagens de validação ou resposta de API.
- **Sempre usar** o módulo `NotificacoesPadrao.js` para feedback ao usuário.
- **Tipos:** `success` | `danger` (erro) | `warning` (aviso) | `info`. O tipo `error` é aceito e tratado como `danger`.

---

## 1. Alertas na página

Mensagens aparecem **logo abaixo da barra de navegação**, em uma área única que não sobrepõe o conteúdo (fica no fluxo da página). Não é necessário incluir nenhum container no template: o `index_Base.html` já possui a área `#notificacoes-global`.

- **Onde:** logo abaixo da navbar; quando há alertas, a área ganha fundo e borda; quando está vazia, não ocupa espaço.
- **Visual:** cada alerta tem rótulo em destaque (Erro, Aviso, Sucesso, Informação), ícone, texto e botão fechar; animação de entrada e sombra.
- Se precisar que os alertas apareçam dentro do conteúdo da própria tela (ex.: dentro de um card), use `opcoes.containerId: 'alertas-container'` e inclua `<div id="alertas-container"></div>` no template.

### No JavaScript

```javascript
// Sucesso
Notificacoes.pagina('Registro salvo com sucesso.', 'success');

// Erro
Notificacoes.pagina('Erro ao conectar na API.', 'danger');
// ou
Notificacoes.pagina('Erro ao conectar.', 'error');

// Aviso
Notificacoes.pagina('Preencha todos os campos obrigatórios.', 'warning');

// Info
Notificacoes.pagina('Carregando dados...', 'info');

// Com opções (container diferente, tempo de auto-fechar)
Notificacoes.pagina('Mensagem', 'success', {
  containerId: 'meu-container',
  autoCloseMs: 8000
});
```

Comportamento: alerta **dismissível** (botão fechar), **auto-removido** após 5 segundos (configurável).

---

## 2. Alertas dentro de modal

**Regra:** Todo erro ou aviso gerado por um processo que foi iniciado **dentro de um modal** (envio de formulário, upload, ação em botão do modal) deve ser exibido **dentro desse mesmo modal**, e não na área fixa da página.

### No HTML (template do modal)

No início do `modal-body`, coloque um container com id único para aquele modal:

```html
<div class="modal-body">
  <div id="modalClienteUpdAlerts"></div>
  <!-- resto do conteúdo do modal -->
</div>
```

Convenção de nome: `modal{Nome}Alerts` (ex.: `modalClienteUpdAlerts`, `modalCargaXmlAlerts`, `modalUploadZipSpedAlerts`).

### No JavaScript

```javascript
// Exibir erro no modal
Notificacoes.modal('Erro ao salvar. Tente novamente.', 'danger', 'modalClienteUpdAlerts');

// Sucesso (auto-fecha em 5s)
Notificacoes.modal('Cliente atualizado com sucesso!', 'success', 'modalClienteUpdAlerts');

// Ao abrir o modal: limpar alertas antigos
Notificacoes.limparModal('modalClienteUpdAlerts');
```

Parâmetros: `Notificacoes.modal(mensagem, tipo, containerId, opcoes)`.  
Em `opcoes`: `limparAntes` (default true), `autoCloseMs`, `comIcone`, `dismissible`.

---

## 3. Resposta de API (JSON)

Quando o backend retorna JSON com erro ou sucesso, use o mesmo padrão:

```javascript
fetch(url, options)
  .then(res => res.json())
  .then(data => {
    if (data.erro) {
      Notificacoes.pagina(data.erro, 'danger');
      // ou no modal:
      Notificacoes.modal(data.erro, 'danger', 'modalXxxAlerts');
      return;
    }
    if (data.success && data.message) {
      Notificacoes.modal(data.message, 'success', 'modalXxxAlerts');
    }
  })
  .catch(err => {
    Notificacoes.pagina('Erro na requisição: ' + err.message, 'danger');
  });
```

Mantenha no backend: `{"erro": "..."}` ou `{"success": true, "message": "..."}` para consistência.

---

## 4. Mensagens do Django (servidor)

As mensagens enviadas com `messages.success()`, `messages.error()`, etc. são exibidas automaticamente no topo do conteúdo (index_Base) com a classe `alert-padrao`.  
A tag `error` do Django é estilizada como “perigo” (vermelho) no CSS base.

---

## 5. Página de login

Na tela de login (fora do layout com sidebar), o erro é exibido com o bloco existente:

```html
{% if error_message %}
<div class="login-error">{{ error_message }}</div>
{% endif %}
```

Mantém-se o padrão visual da própria página de login (Style_Login.css).

---

## Referência rápida

| Contexto      | Função                      | Container (exemplo)        |
|---------------|-----------------------------|----------------------------|
| Página        | `Notificacoes.pagina(...)`  | `#alertas-container`       |
| Modal         | `Notificacoes.modal(..., id)` | `#modalClienteUpdAlerts` |
| Limpar modal  | `Notificacoes.limparModal(id)` | -                      |
| Limpar página | `Notificacoes.limparPagina(id)` | `#alertas-container`   |

Arquivos do padrão:

- **JS:** `app/static/js/NotificacoesPadrao.js`
- **CSS:** `app/static/css/Style_Base.css` (classes `.alert-padrao`, `#alertas-container`)
- **Base:** `app/templates/index_Base.html` (script e Font Awesome incluídos)
