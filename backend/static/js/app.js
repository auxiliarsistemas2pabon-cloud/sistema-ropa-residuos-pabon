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
  // Checklist: cada prenda es una fila con casilla + cantidad + peso (kg)
  // en la misma fila (sin select+botón "Agregar" aparte).
  function iniciarDetallePrendas() {
    var contenedores = document.querySelectorAll("[data-detalle-prendas]");
    contenedores.forEach(function (contenedor) {
      var oculto = contenedor.querySelector("[data-detalle-prenda-oculto]");
      var filas = contenedor.querySelectorAll("[data-detalle-prenda-fila]");
      if (!oculto || !filas.length) return;

      function actualizar() {
        var detalles = [];
        filas.forEach(function (fila) {
          var check = fila.querySelector("[data-detalle-prenda-check]");
          var cantidad = fila.querySelector("[data-detalle-prenda-cantidad-inline]");
          var peso = fila.querySelector("[data-detalle-prenda-peso-inline]");
          cantidad.disabled = !check.checked;
          peso.disabled = !check.checked;
          if (!check.checked) {
            cantidad.value = "";
            peso.value = "";
            return;
          }
          var cantidadVal = parseInt(cantidad.value, 10);
          if (cantidadVal >= 1) {
            var detalle = { prenda: check.value, cantidad_unidades: cantidadVal };
            if (peso.value !== "") detalle.peso_kg = peso.value;
            detalles.push(detalle);
          }
        });
        oculto.value = JSON.stringify(detalles);
      }

      filas.forEach(function (fila) {
        var check = fila.querySelector("[data-detalle-prenda-check]");
        var cantidad = fila.querySelector("[data-detalle-prenda-cantidad-inline]");
        var peso = fila.querySelector("[data-detalle-prenda-peso-inline]");
        check.addEventListener("change", function () {
          if (check.checked) {
            if (!cantidad.value) cantidad.value = "1";
            actualizar();
            cantidad.focus();
            cantidad.select();
          } else {
            actualizar();
          }
        });
        cantidad.addEventListener("input", actualizar);
        peso.addEventListener("input", actualizar);
      });

      actualizar();
    });
  }

  // --- Firma dibujada en pantalla (FR-SIG-86) ---
  // Quien no inició sesión (la otra persona del movimiento) firma con el
  // dedo o el mouse; se guarda como PNG en base64 en el campo oculto.
  function iniciarFirma() {
    var contenedores = document.querySelectorAll("[data-firma]");
    contenedores.forEach(function (contenedor) {
      var canvas = contenedor.querySelector("[data-firma-lienzo]");
      var limpiar = contenedor.querySelector("[data-firma-limpiar]");
      var oculto = contenedor.querySelector("[data-firma-oculta]");
      if (!canvas || !oculto) return;

      var ctx = canvas.getContext("2d");
      var dibujando = false;
      var tieneTrazo = false;

      function fondoBlanco() {
        ctx.fillStyle = "#fff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.lineWidth = 2;
        ctx.lineCap = "round";
        ctx.strokeStyle = "#1a1a1a";
      }
      fondoBlanco();

      function posicion(e) {
        var rect = canvas.getBoundingClientRect();
        return {
          x: (e.clientX - rect.left) * (canvas.width / rect.width),
          y: (e.clientY - rect.top) * (canvas.height / rect.height),
        };
      }

      function empezar(e) {
        e.preventDefault();
        dibujando = true;
        var p = posicion(e);
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
      }

      function trazar(e) {
        if (!dibujando) return;
        e.preventDefault();
        var p = posicion(e);
        ctx.lineTo(p.x, p.y);
        ctx.stroke();
        tieneTrazo = true;
      }

      function terminar() {
        if (!dibujando) return;
        dibujando = false;
        oculto.value = tieneTrazo ? canvas.toDataURL("image/png") : "";
      }

      canvas.addEventListener("pointerdown", empezar);
      canvas.addEventListener("pointermove", trazar);
      canvas.addEventListener("pointerup", terminar);
      canvas.addEventListener("pointerleave", terminar);

      if (limpiar) {
        limpiar.addEventListener("click", function () {
          fondoBlanco();
          tieneTrazo = false;
          oculto.value = "";
        });
      }
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

  // --- Recarga la página al cambiar de sede (RF de servicios por sede) ---
  // El servicio/área depende de la sede y se filtra en el servidor; como no
  // hay recarga parcial para estos formularios (HTMX se reserva para la
  // cascada de residuos), al cambiar de sede se navega de nuevo con
  // ?sede=<id> para traer las opciones correctas — ver _sede_seleccionada()
  // en ropa/forms.py.
  function iniciarRecargaPorSede() {
    var sede = document.getElementById("id_sede");
    if (!sede) return;
    sede.addEventListener("change", function () {
      if (!sede.value) return;
      var params = new URLSearchParams(window.location.search);
      params.set("sede", sede.value);
      window.location.search = params.toString();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    iniciarPesoNeto();
    iniciarDetallePrendas();
    iniciarFirma();
    iniciarPasos();
    iniciarRecargaPorSede();
  });
})();
