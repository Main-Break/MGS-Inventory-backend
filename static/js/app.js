/*
Script da interface web: o modal de confirmação genérico (#modalConfirmacao, em
templates/base.html) e o botão "Calcular peso" do formulário de item
(templates/itens/form.html).
*/

document.addEventListener("DOMContentLoaded", function () {
    iniciarModalConfirmacao();
    iniciarCalculoPeso();
});


function iniciarModalConfirmacao() {
    // Monta o modal a partir dos data-* do botão que abriu ele. Nenhuma chamada de
    // rede acontece aqui: o modal só prepara um <form> comum (method="post"), que
    // envia como qualquer outro formulário da interface.
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
}


function iniciarCalculoPeso() {
    // Chama GET /app/itens/calcular-peso (views/itens.py) com o formato, o material
    // e as medidas já preenchidas no formulário, e usa o resultado para preencher
    // o peso unitário. A fórmula em si mora só no backend (util/calculo_peso.py).
    var botao = document.getElementById("botaoCalcularPeso");
    if (!botao) return;

    botao.addEventListener("click", function () {
        var aviso = document.getElementById("avisoCalculoPeso");
        var shape = document.getElementById("shape").value;
        var materialId = document.getElementById("material_id").value;

        if (!shape || !materialId) {
            aviso.innerHTML = '<div class="alert alert-warning py-2 mb-0">Escolha o formato e o material antes de calcular.</div>';
            return;
        }

        var parametros = new URLSearchParams({
            shape: shape,
            material_id: materialId,
            height_cm: document.getElementById("height_cm").value || 0,
            width_cm: document.getElementById("width_cm").value || 0,
            length_cm: document.getElementById("length_cm").value || 0,
        });

        fetch("/app/itens/calcular-peso?" + parametros.toString())
            .then(function (resposta) {
                if (!resposta.ok) throw new Error("Não foi possível calcular o peso.");
                return resposta.json();
            })
            .then(function (dado) {
                document.getElementById("weight_kg").value = dado.peso_kg;
                aviso.innerHTML = '<div class="alert alert-success py-2 mb-0">Peso calculado: ' + dado.peso_kg + ' kg.</div>';
            })
            .catch(function (erro) {
                aviso.innerHTML = '<div class="alert alert-danger py-2 mb-0">' + erro.message + '</div>';
            });
    });
}
