(function () {
  "use strict";

  function parseKg(valor) {
    return parseFloat(String(valor || "").replace(",", ".")) || 0;
  }

  // --- Peso neto en vivo (10.4) ---
  function iniciarPesoNeto() {
    var total = document.getElementById("id_peso_total");
    var tara = document.getElementById("id_tara");
    var neto = document.querySelector("[data-peso-neto]");
    if (!total || !tara || !neto) return;

    var errorTara = document.querySelector("[data-error-tara]");
    var botones = document.querySelectorAll("[data-requiere-peso-valido]");

    function recalcular() {
      var t = parseKg(total.value);
      var r = parseKg(tara.value);
      var invalido = r > t;
      var sinPeso = t <= 0;

      neto.textContent = invalido || sinPeso ? "—" : (t - r).toFixed(2) + " kg";
      neto.classList.toggle("is-invalido", invalido);
      tara.classList.toggle("is-invalido", invalido);
      if (errorTara) errorTara.hidden = !invalido;
      botones.forEach(function (b) { b.disabled = invalido || sinPeso; });
    }

    total.addEventListener("input", recalcular);
    tara.addEventListener("input", recalcular);
    recalcular();
  }

  // --- Navegación por pasos (10.5: máximo 3 pantallas) ---
  function iniciarPasos() {
    var form = document.querySelector("[data-formulario-pasos]");
    if (!form) return;

    var pasos = Array.prototype.slice.call(form.querySelectorAll("[data-paso]"));
    var puntos = Array.prototype.slice.call(document.querySelectorAll("[data-stepper] .stepper__paso"));

    function mostrar(indice) {
      pasos.forEach(function (p, i) { p.hidden = i !== indice; });
      puntos.forEach(function (li, i) {
        li.classList.toggle("is-actual", i === indice);
        li.classList.toggle("is-hecho", i < indice);
      });
      var primero = pasos[indice].querySelector("input, select, textarea");
      if (primero) primero.focus();
    }

    function indiceActual() {
      return pasos.findIndex(function (p) { return !p.hidden; });
    }

    function pasoValido(paso) {
      var campos = paso.querySelectorAll("input, select, textarea");
      for (var i = 0; i < campos.length; i++) {
        if (!campos[i].checkValidity()) { campos[i].reportValidity(); return false; }
      }
      return true;
    }

    form.addEventListener("click", function (e) {
      if (e.target.matches("[data-siguiente]")) {
        var actual = indiceActual();
        if (pasoValido(pasos[actual])) mostrar(Math.min(actual + 1, pasos.length - 1));
      }
      if (e.target.matches("[data-anterior]")) {
        mostrar(Math.max(indiceActual() - 1, 0));
      }
    });

    // Si el servidor devolvió errores, abrir el primer paso que los tenga.
    var pasoConError = pasos.findIndex(function (p) { return p.querySelector(".campo--error"); });
    mostrar(pasoConError >= 0 ? pasoConError : 0);
  }

  document.addEventListener("DOMContentLoaded", function () {
    iniciarPesoNeto();
    iniciarPasos();
  });
})();
