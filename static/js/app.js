/*
Script da interface web. Só uma coisa: monta o modal de confirmação
genérico (#modalConfirmacao, em templates/base.html) a partir dos data-*
do botão que abriu ele, antes de aparecer na tela.

Nenhuma chamada de rede acontece aqui: o modal só prepara um <form> comum
(method="post"), que envia como qualquer outro formulário da interface.
*/

document.addEventListener("DOMContentLoaded", function () {
    var modal = document.getElementById("modalConfirmacao");
    if (!modal) return;

    modal.addEventListener("show.bs.modal", function (evento) {
        var botao = evento.relatedTarget;

        document.getElementById("modalConfirmacaoMensagem").textContent = botao.getAttribute("data-mensagem");
        document.getElementById("modalConfirmacaoForm").setAttribute("action", botao.getAttribute("data-action"));

        var campo = document.getElementById("modalConfirmacaoCampo");
        campo.setAttribute("name", botao.getAttribute("data-campo") || "new_status");
        campo.value = botao.getAttribute("data-valor");

        var confirmar = document.getElementById("modalConfirmacaoBotao");
        confirmar.textContent = botao.getAttribute("data-botao-texto") || "Confirmar";
        confirmar.className = "btn " + (botao.getAttribute("data-botao-classe") || "btn-danger");
    });
});
