/*
Tela de nova verificação (templates/verifications/nova.html). Fluxo em dois passos:
1. Escolher o método (cards #passoMetodo): selecionar item, escanear código de
   barras, ou deixar a IA identificar tudo pela foto.
2. Formulário certo pro método escolhido (#passoFormulario), sempre terminando na
   foto - é o que POST /app/verificacoes/nova espera (mesma regra de
   core.py::create_verification_from_photo, usada também pela API).

Leitura de código de barras pela BarcodeDetector API nativa do navegador
(Chrome/Edge, sem biblioteca externa). Sem suporte, o método "código de barras"
avisa e sugere escolher "Selecionar item".
*/

document.addEventListener("DOMContentLoaded", function () {
    iniciarEscolhaDeMetodo();
    iniciarPreviewFoto();
});


function iniciarEscolhaDeMetodo() {
    var passoMetodo = document.getElementById("passoMetodo");
    var passoFormulario = document.getElementById("passoFormulario");
    var botaoTrocar = document.getElementById("botaoTrocarMetodo");
    if (!passoMetodo || !passoFormulario) return;

    var blocoCodigoBarras = document.getElementById("blocoCodigoBarras");
    var blocoSelecionarItem = document.getElementById("blocoSelecionarItem");
    var blocoFoto = document.getElementById("blocoFoto");
    var botaoEnviar = document.getElementById("botaoEnviar");
    var itemIdentificado = document.getElementById("itemIdentificado");
    var itemIdHidden = document.getElementById("item_id");
    var itemIdSelect = document.getElementById("item_id_select");

    itemIdSelect.addEventListener("change", function () {
        itemIdHidden.value = itemIdSelect.value;
    });

    passoMetodo.querySelectorAll(".card-metodo").forEach(function (card) {
        card.addEventListener("click", function () {
            escolherMetodo(card.getAttribute("data-metodo"));
        });
    });

    botaoTrocar.addEventListener("click", function () {
        pararScanner();
        passoFormulario.classList.add("d-none");
        passoMetodo.classList.remove("d-none");
        itemIdHidden.value = "";
        itemIdSelect.value = "";
        itemIdentificado.classList.add("d-none");
    });

    function esconderTudo() {
        [blocoCodigoBarras, blocoSelecionarItem, blocoFoto, botaoEnviar, itemIdentificado].forEach(function (el) {
            el.classList.add("d-none");
        });
    }

    function escolherMetodo(metodo) {
        passoMetodo.classList.add("d-none");
        passoFormulario.classList.remove("d-none");
        esconderTudo();

        if (metodo === "manual") {
            blocoSelecionarItem.classList.remove("d-none");
            blocoFoto.classList.remove("d-none");
            botaoEnviar.classList.remove("d-none");
        } else if (metodo === "codigo") {
            blocoCodigoBarras.classList.remove("d-none");
            iniciarScanner();
        } else if (metodo === "ia") {
            blocoFoto.classList.remove("d-none");
            botaoEnviar.classList.remove("d-none");
        }
    }

    var streamAtivo = null;
    var escaneando = false;

    function iniciarScanner() {
        var video = document.getElementById("videoScanner");
        var aviso = document.getElementById("avisoScanner");
        video.classList.remove("d-none");
        aviso.innerHTML = "";

        if (!("BarcodeDetector" in window)) {
            aviso.innerHTML = '<span class="text-danger">Este navegador não lê código de barras pela câmera. Volte e escolha "Selecionar item".</span>';
            return;
        }

        navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
            .then(function (stream) {
                streamAtivo = stream;
                video.srcObject = stream;
                video.play();
                escaneando = true;
                aviso.innerHTML = '<span class="text-muted">Aponte a câmera para o código de barras da etiqueta.</span>';
                procurarCodigo(new BarcodeDetector(), video, aviso);
            })
            .catch(function () {
                aviso.innerHTML = '<span class="text-danger">Não foi possível acessar a câmera. Volte e escolha "Selecionar item".</span>';
            });
    }

    function pararScanner() {
        escaneando = false;
        if (streamAtivo) {
            streamAtivo.getTracks().forEach(function (track) { track.stop(); });
            streamAtivo = null;
        }
    }

    function procurarCodigo(detector, video, aviso) {
        if (!escaneando) return;

        detector.detect(video)
            .then(function (codigos) {
                if (codigos.length > 0) {
                    buscarItemPorCodigo(codigos[0].rawValue, aviso);
                    return;
                }
                requestAnimationFrame(function () { procurarCodigo(detector, video, aviso); });
            })
            .catch(function () {
                requestAnimationFrame(function () { procurarCodigo(detector, video, aviso); });
            });
    }

    function buscarItemPorCodigo(codigo, aviso) {
        fetch("/app/itens/buscar-por-codigo?barcode=" + encodeURIComponent(codigo))
            .then(function (resposta) {
                if (!resposta.ok) throw new Error("Nenhum item com o código " + codigo + ".");
                return resposta.json();
            })
            .then(function (item) {
                itemIdHidden.value = item.id;
                itemIdentificado.textContent = "Item identificado: " + item.name;
                itemIdentificado.classList.remove("d-none");
                blocoFoto.classList.remove("d-none");
                botaoEnviar.classList.remove("d-none");
                pararScanner();
                document.getElementById("videoScanner").classList.add("d-none");
            })
            .catch(function (erro) {
                aviso.innerHTML = '<span class="text-danger">' + erro.message + ' Tentando de novo...</span>';
                requestAnimationFrame(function () { procurarCodigo(new BarcodeDetector(), document.getElementById("videoScanner"), aviso); });
            });
    }
}


function iniciarPreviewFoto() {
    var input = document.getElementById("arquivo");
    var preview = document.getElementById("previewFoto");
    if (!input || !preview) return;

    input.addEventListener("change", function () {
        var arquivo = input.files[0];
        if (!arquivo) {
            preview.classList.add("d-none");
            return;
        }

        preview.src = URL.createObjectURL(arquivo);
        preview.classList.remove("d-none");
    });
}
