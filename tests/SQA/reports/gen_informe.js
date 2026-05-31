// Generador del Informe de Pruebas (US01 + US04) — Snipe-IT SQA
// Uso: node gen_informe.js
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, TableOfContents, LevelFormat,
} = require("docx");

const OUT = "Informe de Pruebas - US01 y US04.docx";

// ---------- Paleta / helpers ----------
const FONT = "Arial";
const BLUE = "2E75B6";
const GREY = "CCCCCC";
const HEAD_FILL = "D5E8F0";
const PASS_FILL = "E2EFDA";
const FAIL_FILL = "FCE4E4";
const CODE_FILL = "F2F2F2";

const border = { style: BorderStyle.SINGLE, size: 1, color: GREY };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 110, right: 110 };

function txt(text, opts = {}) { return new TextRun({ text, font: FONT, ...opts }); }

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120, ...(opts.spacing || {}) },
    alignment: opts.alignment,
    children: Array.isArray(text) ? text : [txt(text, opts.run || {})],
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    children: Array.isArray(text) ? text : [txt(text)],
    spacing: { after: 60 },
  });
}

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 280, after: 160 },
    children: [txt(text, { bold: true, size: 30, color: BLUE })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 120 },
    children: [txt(text, { bold: true, size: 26, color: "1F4E79" })] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 160, after: 100 },
    children: [txt(text, { bold: true, size: 23, color: "1F4E79" })] });
}

// Bloque de código tipo CLI/código, conservando monoespaciado y saltos
function codeBlock(code) {
  const lines = code.replace(/\t/g, "    ").split("\n");
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [ new TableRow({ children: [ new TableCell({
      borders, width: { size: 9360, type: WidthType.DXA },
      shading: { fill: CODE_FILL, type: ShadingType.CLEAR },
      margins: { top: 120, bottom: 120, left: 160, right: 160 },
      children: lines.map((ln) => new Paragraph({
        spacing: { after: 0 },
        children: [new TextRun({ text: ln || " ", font: "Consolas", size: 17 })],
      })),
    }) ] }) ],
  });
}

// Tabla genérica: headers (array) + rows (array de arrays). colW en DXA.
function table(headers, rows, colW, rowFills = []) {
  const total = colW.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((htext, i) => new TableCell({
      borders, width: { size: colW[i], type: WidthType.DXA },
      shading: { fill: HEAD_FILL, type: ShadingType.CLEAR }, margins: cellMargins,
      children: [new Paragraph({ children: [txt(htext, { bold: true, size: 19 })] })],
    })),
  });
  const bodyRows = rows.map((r, ri) => new TableRow({
    children: r.map((c, i) => new TableCell({
      borders, width: { size: colW[i], type: WidthType.DXA },
      shading: rowFills[ri] ? { fill: rowFills[ri], type: ShadingType.CLEAR } : undefined,
      margins: cellMargins,
      children: (Array.isArray(c) ? c : [c]).map((line) =>
        new Paragraph({ children: [txt(String(line), { size: 18 })], spacing: { after: 0 } })),
    })),
  }));
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: colW,
    rows: [headerRow, ...bodyRows] });
}

function spacer() { return new Paragraph({ spacing: { after: 80 }, children: [txt("")] }); }

// ---------- Datos ----------
const us04Cases = [
  ["CP-HU04-01", "Checkout exitoso con cupos disponibles", "Sistema", "Partición de equivalencia", "Alta", "Pass"],
  ["CP-HU04-02", "Checkout exitoso con último cupo disponible", "Sistema", "Análisis de valores límite", "Alta", "Pass"],
  ["CP-HU04-03", "Licencia sin cupos no permite checkout", "Sistema", "Prueba negativa / estado", "Alta", "Pass"],
  ["CP-HU04-04", "Intento forzado de checkout sin cupos", "Sistema", "Prueba negativa / forzado", "Media", "Pass"],
  ["CP-HU04-05", "Validación de \"Checkout to\" vacío", "Sistema", "Partición de equivalencia", "Alta", "Pass"],
  ["CP-HU04-06", "Cancelación del checkout antes de confirmar", "Sistema", "Validación de cancelación", "Media", "Pass"],
  ["CP-HU04-07", "Usuario sin permisos no puede hacer checkout", "Sistema", "Control de permisos", "Alta", "Pass"],
  ["CP-HU04-08", "Usuario no autenticado no accede al flujo", "Sistema", "Control de permisos", "Media", "Pass"],
  ["CP-HU04-09", "Persistencia de contadores tras refrescar", "Sistema", "Persistencia de estado", "Media", "Pass"],
  ["CP-HU04-10", "Prevención de doble envío del checkout", "Sistema", "Prueba negativa / integridad", "Alta", "Pass"],
  ["CP-HU04-11", "Checkout se refleja en el perfil del usuario", "Integración", "Consistencia entre módulos", "Alta", "Pass"],
  ["CP-HU04-12", "Checkout bloqueado no aparece en el perfil", "Integración", "Prueba negativa / consistencia", "Media", "Pass"],
  ["CP-HU04-13", "Consistencia detalle vs. listado tras checkout", "Integración", "Consistencia entre vistas", "Media", "Pass"],
  ["CP-HU04-14", "Consistencia de \"No Seats Available\"", "Integración", "Consistencia entre vistas", "Alta", "Pass"],
  ["CP-HU04-15", "Usabilidad y navegación por teclado", "Sistema", "Exploratoria / experiencia", "Media", "Pass"],
];

const us01Cases = [
  ["CP-HU01-01", "Creación exitosa con estado Ready to Deploy", "Sistema", "Partición de equivalencia", "Alta", "Pass"],
  ["CP-HU01-02", "Creación con Asset Name de 255 caracteres", "Sistema", "Análisis de valores límite", "Media", "Fail (DEF-US01-01)"],
  ["CP-HU01-02b", "Creación con Asset Name de 191 (límite real)", "Sistema", "Análisis de valores límite", "Media", "Pass"],
  ["CP-HU01-03", "Bloqueo de creación con serial duplicado", "Sistema", "Prueba negativa / unicidad", "Alta", "Pass"],
  ["CP-HU01-04", "No permite guardar sin Status Label", "Sistema", "Prueba negativa", "Alta", "Pass"],
  ["CP-HU01-05", "El activo creado aparece en el listado", "Integración", "Consistencia entre módulos", "Alta", "Pass"],
];

function fillFor(result) { return result.startsWith("Pass") ? PASS_FILL : FAIL_FILL; }

// ---------- Fragmentos de código (extraídos de los archivos del proyecto) ----------
const CODE_API_HELPER =
`def _api(method, endpoint, data=None, retries=3):
    """Calls the Snipe-IT REST API. Retries up to 3 times on 429 (rate limit)."""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    url = f"{BASE_URL}/api/v1{endpoint}"
    for attempt in range(retries):
        resp = requests.request(method, url, json=data, headers=headers, timeout=10)
        if resp.status_code == 429 and attempt < retries - 1:
            time.sleep(8 * (attempt + 1))   # 8s, 16s
            continue
        resp.raise_for_status()
        return resp.json()`;

const CODE_SELECT2 =
`def select_user(self, user_id, user_name=""):
    """Sets the 'Checkout to' Select2 to the given user (AJAX data source)."""
    self.page.wait_for_selector("#assigned_user_select", state="attached", timeout=5000)
    self.page.evaluate(
        """([userId, userName]) => {
            var select = document.getElementById('assigned_user_select');
            var opt = new Option(userName, userId, true, true);
            select.add(opt);
            if (window.$ && $(select).data('select2')) {
                $(select).val(userId).trigger('change');
            } else {
                select.value = userId;
                select.dispatchEvent(new Event('change', {bubbles: true}));
            }
        }""",
        [str(user_id), user_name],
    )`;

const CODE_REVEAL =
`# El form de creación de activos (Snipe-IT v8) oculta campos en la sección
# colapsable "Optional Information" (div#optional_details, display:none).
_REVEAL_SECTIONS_JS = """() => {
    const opt = document.getElementById('optional_details');
    if (opt) { opt.style.display = 'block'; }
    document.querySelectorAll('.collapse').forEach(c => {
        c.style.display = 'block'; c.classList.add('in', 'show');
    });
}"""`;

const CODE_UNIQUE_SERIAL =
`@pytest.fixture
def unique_serial_enabled():
    """Activa el ajuste 'unique_serial' (necesario para CP-HU01-03) y lo
    restaura al valor original al finalizar."""
    original = _get_unique_serial()
    if original != 1:
        _set_unique_serial(1)
    yield
    _set_unique_serial(original)`;

const CODE_TOKEN =
`docker exec snipeit-app-1 bash -c 'cat > /tmp/gen_token.php << PHPEOF
<?php
$user = App\\Models\\User::find(1);
$token = $user->createToken("SQA-US04-Tests");
echo "TOKEN:" . $token->accessToken;
PHPEOF
php /var/www/html/artisan tinker --execute="require '/tmp/gen_token.php';"'`;

const CODE_RUN =
`# US04 (14 casos automatizados + 1 manual)
pytest automated/ -v --html=reports/2026-05-30_US04_execution_report.html --self-contained-html

# US01 (5 casos + 1 complementario)
pytest automated/ -v --html=reports/2026-05-30_US01_execution_report.html --self-contained-html`;

// ---------- Documento ----------
const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: FONT, color: BLUE },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: "1F4E79" },
        paragraph: { spacing: { before: 220, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: FONT, color: "1F4E79" },
        paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 520, hanging: 260 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 980, hanging: 260 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [ new Paragraph({
      alignment: AlignmentType.RIGHT,
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE, space: 1 } },
      children: [txt("Informe de Pruebas — Snipe-IT SQA", { size: 16, color: "808080" })] }) ] }) },
    footers: { default: new Footer({ children: [ new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [ txt("Página ", { size: 16, color: "808080" }),
        new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "808080" }) ] }) ] }) },
    children: [
      // Portada
      new Paragraph({ spacing: { before: 1600, after: 0 }, alignment: AlignmentType.CENTER,
        children: [txt("Informe de Pruebas", { bold: true, size: 56, color: BLUE })] }),
      new Paragraph({ spacing: { before: 120, after: 0 }, alignment: AlignmentType.CENTER,
        children: [txt("Proyecto Snipe-IT — Aseguramiento de la Calidad del Software", { size: 26, color: "595959" })] }),
      new Paragraph({ spacing: { before: 80, after: 0 }, alignment: AlignmentType.CENTER,
        children: [txt("US01 – Creación de Activos  |  US04 – Checkout de Licencias", { size: 22, color: "595959" })] }),
      new Paragraph({ spacing: { before: 900, after: 0 }, alignment: AlignmentType.CENTER,
        children: [txt("Responsable: Aarón Líos Cubillo", { size: 22 })] }),
      new Paragraph({ spacing: { before: 60 }, alignment: AlignmentType.CENTER,
        children: [txt("Fecha: 30 de mayo de 2026", { size: 22 })] }),
      new Paragraph({ spacing: { before: 60 }, alignment: AlignmentType.CENTER,
        children: [txt("Versión del sistema bajo prueba: Snipe-IT v8.4.0 (build 21690)", { size: 20, color: "595959" })] }),
      new Paragraph({ pageBreakBefore: true, children: [txt("Tabla de contenido", { bold: true, size: 28, color: BLUE })], spacing: { after: 160 } }),
      new TableOfContents("Tabla de contenido", { hyperlink: true, headingStyleRange: "1-3" }),

      // ===================== 2. RESULTADOS =====================
      new Paragraph({ pageBreakBefore: true, heading: HeadingLevel.HEADING_1,
        children: [txt("2. Resultados", { bold: true, size: 30, color: BLUE })] }),
      p([txt("Este apartado presenta los resultados obtenidos tras la ejecución de los casos de prueba "
        + "diseñados para las historias de usuario US01 (Creación de Activos) y US04 (Checkout de "
        + "Licencias). La totalidad de las pruebas funcionales se implementó como pruebas de sistema e "
        + "integración bajo la técnica de caja negra, automatizadas con ")]),
      p([txt("Python 3.12 + pytest + Playwright", { bold: true }),
        txt(" sobre la instancia local de Snipe-IT (Docker, "),
        txt("http://localhost:8000", { font: "Consolas", size: 19 }),
        txt("). Las aserciones de estado se verifican contra la API REST de Snipe-IT como fuente de "
          + "verdad, dado que las tablas de la interfaz se cargan de forma asíncrona (Bootstrap Table).")]),

      h2("2.1. Entorno de ejecución"),
      table(
        ["Componente", "Detalle"],
        [
          ["Sistema bajo prueba", "Snipe-IT v8.4.0 (build 21690), desplegado en Docker"],
          ["URL base", "http://localhost:8000"],
          ["Base de datos", "MariaDB 11.4.7 (contenedor snipeit-db-1)"],
          ["Lenguaje / framework de pruebas", "Python 3.12, pytest 9.x, pytest-playwright"],
          ["Navegador de automatización", "Chromium (Playwright), 1920×1080"],
          ["Sistema operativo", "Windows 10 Pro"],
          ["Técnica de diseño", "Caja negra: partición de equivalencia, valores límite, prueba negativa"],
        ],
        [2600, 6760],
      ),
      spacer(),

      h2("2.2. Pruebas funcionales — US04: Checkout de Licencias"),
      p([txt("La US04 comprende 15 casos de prueba: 14 automatizados y 1 de ejecución manual "
        + "(CP-HU04-15, exploratorio de usabilidad). Resultado global: "),
        txt("15/15 aprobados (100 %).", { bold: true })]),
      table(
        ["ID", "Nombre", "Tipo", "Técnica", "Prior.", "Resultado"],
        us04Cases,
        [1280, 2860, 1180, 2060, 820, 1160],
        us04Cases.map((c) => fillFor(c[5])),
      ),
      spacer(),
      p([txt("Los casos CP-HU04-01 a 14 se ejecutaron de forma automatizada (reporte "),
        txt("reports/2026-05-30_US04_execution_report.html", { font: "Consolas", size: 18 }),
        txt("). El caso CP-HU04-15 se ejecutó de forma manual asistida por navegador, registrando el "
          + "orden de foco por teclado y capturando evidencia gráfica del flujo.")]),

      h2("2.3. Pruebas funcionales — US01: Creación de Activos"),
      p([txt("La US01 comprende 5 casos de prueba definidos en el plan, automatizados en su totalidad. "
        + "Adicionalmente se incorporó el caso complementario CP-HU01-02b para documentar el límite real "
        + "del sistema. Resultado global: "),
        txt("5 aprobados, 1 fallido (defecto DEF-US01-01).", { bold: true })]),
      table(
        ["ID", "Nombre", "Tipo", "Técnica", "Prior.", "Resultado"],
        us01Cases,
        [1320, 2820, 1180, 2040, 820, 1180],
        us01Cases.map((c) => fillFor(c[5])),
      ),
      spacer(),
      p([txt("El caso CP-HU01-02 detectó una discrepancia entre la especificación del plan de pruebas "
        + "(límite de 255 caracteres en Asset Name) y el comportamiento real del sistema (191 "
        + "caracteres). Se documenta como defecto DEF-US01-01 en el apartado 3. El caso CP-HU01-02b "
        + "confirma que el sistema acepta correctamente el límite real de 191 caracteres.")]),

      h2("2.4. Resumen cuantitativo"),
      table(
        ["Historia de usuario", "Diseñados", "Ejecutados", "Aprobados", "Fallidos", "% éxito"],
        [
          ["US04 – Checkout de Licencias", "15", "15", "15", "0", "100 %"],
          ["US01 – Creación de Activos", "6", "6", "5", "1", "83 %"],
          ["Total", "21", "21", "20", "1", "95 %"],
        ],
        [3360, 1300, 1300, 1200, 1100, 1100],
        ["", "", HEAD_FILL],
      ),
      spacer(),
      p([txt("Nota: US01 contabiliza 6 casos al incluir el complementario CP-HU01-02b. El único caso "
        + "fallido (CP-HU01-02) corresponde a un defecto real del sistema, no a un error de la prueba.")],
        { run: { italics: true, size: 19, color: "595959" } }),

      // ===================== 3. DEFECTOS =====================
      h1("3. Defectos"),
      p([txt("Los defectos se documentan ordenados por el tipo de prueba en que fueron identificados. "
        + "Durante este ciclo se registró un (1) defecto funcional y un (1) hallazgo de configuración.")]),

      h2("3.1. Pruebas de sistema (US01)"),
      h3("DEF-US01-01 — Asset Name limitado a 191 caracteres (el plan asume 255)"),
      table(
        ["Campo", "Detalle"],
        [
          ["ID del defecto", "DEF-US01-01"],
          ["Caso asociado", "CP-HU01-02"],
          ["Módulo", "Assets > Create New — campo Asset Name"],
          ["Severidad", "Baja"],
          ["Prioridad", "Baja"],
          ["Tipo", "Discrepancia especificación vs. sistema"],
          ["Estado", "Abierto / Documentado"],
        ],
        [2400, 6960],
      ),
      spacer(),
      p([txt("Descripción: ", { bold: true }),
        txt("el plan de pruebas define, mediante análisis de valores límite, que el límite superior "
          + "válido del campo Asset Name es de 255 caracteres. Sin embargo, la instancia real de Snipe-IT "
          + "limita ese campo a 191 caracteres: el control HTML posee el atributo "),
        txt("maxlength=\"191\"", { font: "Consolas", size: 19 }),
        txt(" y la columna de base de datos "),
        txt("assets.name", { font: "Consolas", size: 19 }),
        txt(" es de tipo "),
        txt("varchar(191)", { font: "Consolas", size: 19 }),
        txt(". En consecuencia, el sistema impide ingresar más de 191 caracteres y, ante un valor mayor, "
          + "lo almacena truncado.")]),
      p([txt("Resultado esperado (plan): ", { bold: true }),
        txt("el sistema acepta y almacena un Asset Name de exactamente 255 caracteres.")]),
      p([txt("Resultado obtenido: ", { bold: true }),
        txt("el campo no admite más de 191 caracteres; el activo se crea con el nombre truncado a 191. "
          + "Salida de la automatización:")]),
      codeBlock("AssertionError: El nombre almacenado no tiene 255 caracteres: 191\nassert 191 == 255"),
      spacer(),
      p([txt("Análisis: ", { bold: true }),
        txt("no se trata de un fallo del flujo de creación (el activo se crea correctamente), sino de una "
          + "discrepancia entre la especificación de prueba y el límite real del sistema. El valor 191 "
          + "corresponde al límite histórico de índices utf8mb4 en MySQL/MariaDB adoptado por Laravel.")]),
      p([txt("Recomendación: ", { bold: true }),
        txt("ajustar el plan de pruebas para fijar el límite superior de Asset Name en 191 caracteres "
          + "(validado por el caso complementario CP-HU01-02b). Si el negocio requiriera 255, debe abrirse "
          + "una solicitud de cambio sobre Snipe-IT, lo cual excede el alcance de QA.")]),

      h2("3.2. Hallazgos de configuración"),
      h3("HALL-US01-01 — La unicidad de serial depende del ajuste unique_serial"),
      p([txt("Durante el diseño de CP-HU01-03 se determinó que Snipe-IT "),
        txt("no obliga seriales únicos de forma predeterminada", { bold: true }),
        txt(" (el ajuste "),
        txt("unique_serial", { font: "Consolas", size: 19 }),
        txt(" tiene valor 0). Para que el sistema rechace seriales duplicados —y el caso de prueba sea "
          + "válido— dicho ajuste debe estar activado. La automatización gestiona este pre-requisito "
          + "activando el ajuste antes de la prueba y restaurándolo al finalizar. Con el ajuste activo, el "
          + "sistema responde correctamente: ")]),
      codeBlock("The serial must be unique."),
      spacer(),
      p([txt("Recomendación: ", { bold: true }),
        txt("si la organización requiere unicidad de seriales, habilitar el ajuste unique_serial en la "
          + "configuración de Snipe-IT (Admin > Settings).")]),

      h2("3.3. Pruebas de US04"),
      p([txt("No se identificaron defectos en la US04. Los 15 casos de prueba se ejecutaron conforme a lo "
        + "esperado, incluyendo los escenarios negativos (sin cupos, sin permisos, sin autenticación, doble "
        + "envío) y los de integración entre el detalle de licencia, el listado y el perfil de usuario.")]),

      // ===================== 5. RECOMENDACIONES =====================
      h1("5. Recomendaciones"),
      bullet([txt("Actualizar el plan de pruebas ", { bold: true }),
        txt("para alinear el valor límite de Asset Name (US01) a 191 caracteres, conforme al "
          + "comportamiento real del sistema (DEF-US01-01).")]),
      bullet([txt("Habilitar unique_serial ", { bold: true }),
        txt("en la configuración de Snipe-IT si la gestión de activos requiere seriales únicos; de lo "
          + "contrario, documentar explícitamente que los seriales duplicados son admisibles.")]),
      bullet([txt("Mantener la verificación por API ", { bold: true }),
        txt("como fuente de verdad en la automatización, dado que las tablas de la interfaz se cargan de "
          + "forma asíncrona y no son fiables para aserciones directas sobre el DOM.")]),
      bullet([txt("Aislar los datos de prueba ", { bold: true }),
        txt("mediante fixtures que creen y eliminen sus propios recursos (licencias, usuarios, activos, "
          + "datos maestros), preservando el estado de la instancia entre ejecuciones.")]),
      bullet([txt("Controlar el límite de tasa (HTTP 429) ", { bold: true }),
        txt("de la API con reintentos espaciados, tal como implementa el helper _api del proyecto, para "
          + "evitar fallos intermitentes en suites con alto volumen de operaciones.")]),
      bullet([txt("Extender la cobertura ", { bold: true }),
        txt("a las historias de usuario restantes y consolidar, en un ciclo posterior, las secciones de "
          + "Introducción, Evaluación y Referencias del informe una vez completadas todas las US.")]),

      // ===================== 7. ANEXOS =====================
      new Paragraph({ pageBreakBefore: true, heading: HeadingLevel.HEADING_1,
        children: [txt("7. Anexos", { bold: true, size: 30, color: BLUE })] }),

      h2("7.1. Estructura del proyecto de pruebas"),
      p("El apartado de SQA se organiza por historia de usuario, separando las pruebas propias de las "
        + "que ya incluía el proyecto original. Cada carpeta de US es autocontenida:"),
      codeBlock(
`tests/SQA/
├── US01-TestCases/
│   ├── conftest.py            (fixtures: auth, datos maestros, unique_serial)
│   ├── pytest.ini
│   ├── pages/                 (Page Object Models)
│   │   ├── login_page.py
│   │   ├── asset_create_page.py
│   │   └── asset_list_page.py
│   ├── automated/             (test_hu01_*.py)
│   ├── cases/                 (CP-HU01-01..05 .md)
│   ├── evidence/              (DEF-US01-01, capturas)
│   └── reports/               (reporte HTML de ejecución)
└── US04-TestCases/
    ├── conftest.py
    ├── pages/                 (login, license_detail, checkout, license_list, user_profile)
    ├── automated/             (test_hu04_*.py)
    ├── cases/                 (CP-HU04-01..15 .md)
    ├── evidence/              (capturas CP-HU04-15)
    └── reports/               (reporte HTML de ejecución)`),
      spacer(),

      h2("7.2. Código fuente del proyecto de pruebas automáticas"),
      p("Se incluyen los fragmentos más representativos de las soluciones técnicas aplicadas, extraídos "
        + "directamente de los archivos del proyecto."),

      h3("7.2.1. Cliente de API con control de límite de tasa (conftest.py)"),
      p("Helper central usado por ambas US para preparar datos y verificar estado contra la API REST, "
        + "con reintentos ante el código HTTP 429:"),
      codeBlock(CODE_API_HELPER),
      spacer(),

      h3("7.2.2. Interacción con el componente Select2 vía AJAX (checkout_page.py)"),
      p("El campo «Checkout to» es un Select2 con origen de datos asíncrono; se controla mediante la API "
        + "de jQuery/Select2 inyectada con page.evaluate():"),
      codeBlock(CODE_SELECT2),
      spacer(),

      h3("7.2.3. Revelado de la sección colapsable del formulario de activos (asset_create_page.py)"),
      p("El formulario de creación de activos (Snipe-IT v8) oculta varios campos —incluido Asset Name— "
        + "en una sección colapsable; se revelan por JavaScript antes de interactuar:"),
      codeBlock(CODE_REVEAL),
      spacer(),

      h3("7.2.4. Gestión del ajuste unique_serial (conftest.py)"),
      p("Fixture que activa el ajuste de unicidad de serial requerido por CP-HU01-03 y lo restaura al "
        + "valor original al terminar:"),
      codeBlock(CODE_UNIQUE_SERIAL),
      spacer(),

      h3("7.2.5. Ejemplo de caso automatizado (test_hu04_01_02_checkout_basic.py)"),
      p("Caso CP-HU04-01: checkout exitoso con cupos disponibles, verificando mensaje y contadores:"),
      codeBlock(
`@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu04_01_checkout_exitoso_con_cupos_disponibles(
    auth_page, base_url, license_2_seats, user_juan
):
    lic_id   = license_2_seats["id"]
    detail   = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    assert get_free_seats(lic_id) == 2
    checked_out_before = get_checked_out_count(lic_id)

    detail.navigate_to_checkout(lic_id)
    assert checkout.is_checkout_form_visible()
    checkout.select_user(user_juan["id"], user_juan.get("name", "Juan Perez"))
    checkout.submit()

    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower()
    assert get_free_seats(lic_id) == 1
    assert get_checked_out_count(lic_id) == checked_out_before + 1`),
      spacer(),

      h2("7.3. Comandos de ejecución"),
      p("Generación de la instancia de API token (una sola vez) dentro del contenedor de aplicación:"),
      codeBlock(CODE_TOKEN),
      spacer(),
      p("Ejecución de las suites y generación de reportes HTML autocontenidos:"),
      codeBlock(CODE_RUN),
      spacer(),

      h2("7.4. Formato de defectos"),
      p("Los defectos se documentan con la plantilla del proyecto, registrando: identificador, caso de "
        + "prueba asociado, módulo, severidad, prioridad, tipo, estado, descripción, pasos para reproducir, "
        + "resultado esperado, resultado obtenido, evidencia, análisis y recomendaciones. El detalle "
        + "completo de DEF-US01-01 se conserva en "),
      p([txt("tests/SQA/US01-TestCases/evidence/DEF-US01-01_asset_name_length.md", { font: "Consolas", size: 18 })]),

      h2("7.5. Listas de chequeo y evidencia"),
      p("Cada caso de prueba cuenta con su documento individual (plantilla de caso de prueba manual del "
        + "proyecto) en las carpetas cases/, indicando precondiciones, pasos, datos, resultado esperado, "
        + "resultado obtenido, estado y enlace a defecto. La evidencia gráfica del caso manual CP-HU04-15 "
        + "y los reportes HTML de ejecución se conservan en las carpetas evidence/ y reports/ de cada US."),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("Generado:", OUT, "(", buf.length, "bytes )");
});
