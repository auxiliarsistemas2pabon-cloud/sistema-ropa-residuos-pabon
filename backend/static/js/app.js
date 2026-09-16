(function () {
  "use strict";

  function parseKg(valor) {
    return parseFloat(String(valor || "").replace(",", ".")) || 0;
  }

  // --- Peso neto y diferencia del ciclo, en vivo (10.4) ---
  function iniciarPesoNeto() {
    var total = document.getElementById("id_peso_total");
    var tara = document.getElementById("id_tara");
    var neto = document.querySelector("[data-peso-neto]");
    if (!total || !tara || !neto) return;

    var errorTara = document.querySelector("[data-error-tara]");
    var botones = document.querySelectorAll("[data-requiere-peso-valido]");

    var form = total.closest("[data-formulario-pasos]");
    var tieneCiclo = form && form.hasAttribute("data-kg-enviados");
    var kgEnviados = tieneCiclo ? parseKg(form.getAttribute("data-kg-enviados")) : 0;
    var panelDif = document.querySelector("[data-diferencia]");
    var obsDif = document.querySelector("[data-obs-diferencia]");

    function recalcular() {
      var t = parseKg(total.value);
      var r = parseKg(tara.value);
      var invalido = r > t;
      var sinPeso = t <= 0;
      var netoKg = t - r;

      neto.textContent = invalido || sinPeso ? "—" : netoKg.toFixed(2) + " kg";
      neto.classList.toggle("is-invalido", invalido);
      tara.classList.toggle("is-invalido", invalido);
      if (errorTara) errorTara.hidden = !invalido;
      botones.forEach(function (b) { b.disabled = invalido || sinPeso; });

      if (!tieneCiclo || !panelDif) return;
      if (invalido || sinPeso) { panelDif.hidden = true; if (obsDif) obsDif.hidden = true; return; }

      var saldo = kgEnviados - netoKg;
      panelDif.hidden = false;
      panelDif.querySelector("[data-dif-enviado]").textContent = kgEnviados.toFixed(2) + " kg";
      panelDif.querySelector("[data-dif-recibido]").textContent = netoKg.toFixed(2) + " kg";
      var saldoEl = panelDif.querySelector("[data-dif-saldo]");
      var hayDif = Math.abs(saldo) >= 0.005;
      saldoEl.textContent = hayDif
        ? Math.abs(saldo).toFixed(2) + " kg " + (saldo > 0 ? "de menos" : "de más")
        : "sin diferencia";
      panelDif.classList.toggle("is-alerta", hayDif);
      if (obsDif) obsDif.hidden = !hayDif;
    }

    total.addEventListener("input", recalcular);
    tara.addEventListener("input", recalcular);
    recalcular();
  }

  // --- Detalle por prenda con selección múltiple (RF-011/012) ---
  function iniciarDetallePrendas() {
    var contenedores = document.querySelectorAll("[data-detalle-prendas]");
    contenedores.forEach(function (contenedor) {
      var select = contenedor.querySelector("[data-detalle-prenda-select]");
      var cantidad = contenedor.querySelector("[data-detalle-prenda-cantidad]");
      var boton = contenedor.querySelector("[data-detalle-prenda-agregar]");
      var lista = contenedor.querySelector("[data-detalle-prenda-lista]");
      var oculto = contenedor.querySelector("[data-detalle-prenda-oculto]");
      var error = contenedor.querySelector("[data-detalle-prenda-error]");
      if (!select || !cantidad || !boton || !lista || !oculto) return;

      var items = [];

      function mostrarError(mensaje) {
        if (!error) return;
        error.textContent = mensaje || "";
        error.hidden = !mensaje;
      }

      function renderizar() {
        lista.innerHTML = "";
        items.forEach(function (item, indice) {
          var li = document.createElement("li");
          li.className = "detalle-prendas__item";

          var texto = document.createElement("span");
          texto.textContent = item.nombre + " · " + item.cantidad_unidades + " uds";

          var quitar = document.createElement("button");
          quitar.type = "button";
          quitar.className = "boton boton--texto";
          quitar.textContent = "Quitar";
          quitar.addEventListener("click", function () {
            items.splice(indice, 1);
            renderizar();
          });

          li.appendChild(texto);
          li.appendChild(quitar);
          lista.appendChild(li);
        });
        oculto.value = JSON.stringify(items.map(function (i) {
          return { prenda: i.prenda, cantidad_unidades: i.cantidad_unidades };
        }));
      }

      boton.addEventListener("click", function () {
        var prendaId = select.value;
        var cantidadVal = parseInt(cantidad.value, 10);
        if (!prendaId) { mostrarError("Selecciona una prenda."); return; }
        if (!cantidadVal || cantidadVal < 1) { mostrarError("Escribe una cantidad válida."); return; }
        if (items.some(function (i) { return i.prenda === prendaId; })) {
          mostrarError("Esa prenda ya está en la lista.");
          return;
        }
        mostrarError("");
        items.push({
          prenda: prendaId,
          nombre: select.options[select.selectedIndex].text,
          cantidad_unidades: cantidadVal,
        });
        select.value = "";
        cantidad.value = "";
        select.focus();
        renderizar();
      });

      renderizar();
    });
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
    iniciarDetallePrendas();
    iniciarPasos();
  });
})();
