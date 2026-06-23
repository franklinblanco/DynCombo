# DynCombo — Kits y Combos Dinámicos — Guía rápida (español)

Cómo funciona DynCombo, para tu revisión y uso.

## 1. Crear un kit (en el producto)
1. Abre el producto en **Inventario / Ventas → Productos**.
2. Entra a la pestaña **DynCombo** y activa **Combo Dinámico**.
3. Elige el **modo de precio**: *Suma de los componentes* (recomendado, en vivo)
   o *Precio fijo del combo*.
4. Lista los **componentes** (producto + cantidad). Verás, por componente, su
   precio y costo unitario, los subtotales, y arriba el **Precio del Combo (en
   vivo)** y el **Costo del Combo (en vivo)**.

Al guardar se genera y mantiene sola una **Lista de Materiales tipo "Kit"
(phantom)** a partir de los componentes — no se edita a mano.

## 2. Precio y costo en vivo (nunca se congelan)
El precio y el costo del kit se recalculan a partir de los componentes
**actuales**. Si sube el flete y cambia el costo de un componente, el costo del
kit se mueve solo, sin tocar el kit. (Esta es la deficiencia de los kits nativos
de Odoo, donde el precio queda congelado.)

## 3. En la cotización
- Al agregar el kit, se **expande en sus componentes en vivo** (sin guardar).
- Cada combo tiene un **color** propio para distinguirlos de un vistazo.
- **Arrastra** un producto debajo de un combo para incluirlo, o fuera para
  sacarlo (el color se actualiza). Un kit no se puede meter dentro de otro.
- La línea del kit muestra el **total del kit**; el total del pedido no se
  duplica.
- Todo es editable por cotización: cantidad (los componentes se reescalan en
  vivo), precio, quitar o agregar.
- Al **eliminar** un kit, pregunta si borrar el kit con sus componentes o solo
  el kit (dejando los componentes como líneas sueltas).

## 4. Compras e inventario
Al **comprar** el kit entran al inventario sus **componentes** (no un producto
"kit"), gracias a la Lista de Materiales tipo Kit. La valuación queda sobre los
componentes, a su costo actual.

## 5. Impresión
Una casilla en la cotización, **Mostrar combo completo al imprimir**: marcada
imprime el desglose de cada combo; sin marcar imprime solo la línea del combo.
Aplica al PDF, al correo y al portal.

## 6. Instalación (la realiza quien administra el servidor)
Este módulo tiene **código Python**, así que **no** se instala desde
*Aplicaciones → Importar módulo* (esa opción solo sirve para módulos de datos,
sin código). Se instala desde la **ruta de addons** del servidor:
1. Colocar la carpeta `sale_dynamic_combo` en la ruta de addons.
2. Reiniciar Odoo.
3. *Aplicaciones → Actualizar lista de aplicaciones → buscar "DynCombo" →
   Instalar*.

Dependencias estándar (se instalan solas): **mrp**, **sale_mrp**,
**purchase_mrp**. **Odoo Online (odoo.com) no permite módulos a medida**;
necesita **Odoo.sh** o un servidor propio / on-premise.

## 7. Licencia
Software propietario bajo **OPL-1** (ver `LICENSE`) y el acuerdo de uso
(`EULA.txt`): uso interno del cliente, **prohibida la redistribución/reventa**.

---
*Cualquier duda, me dices. — Franklin*
