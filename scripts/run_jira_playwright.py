import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAYWRIGHT_DIR = PROJECT_ROOT / "metadata" / "jira_automation"
PROFILE_DIR = PLAYWRIGHT_DIR / "playwright_profile"
SCREENSHOT_PATH = PLAYWRIGHT_DIR / "last_error.png"
LOCK_PATH = PLAYWRIGHT_DIR / "playwright.lock"
LOGIN_WAIT_SECONDS = 600
CREATE_POLL_SECONDS = 2
CREATE_LINK_SELECTOR = "#create_link, a[href*='CreateIssue!default.jspa']"
CREATE_ISSUE_PATH = "/secure/CreateIssue!default.jspa"
NAVIGATION_TIMEOUT_MS = 120000
FORM_READY_TIMEOUT_MS = 90000


def extraer_issue_key_desde_url(url):

    match = re.search(
        r"/browse/([A-Z][A-Z0-9]+-\d+)",
        str(url or "")
    )

    return match.group(1) if match else ""


def obtener_locator_create(page):

    try:

        locator = page.locator(
            CREATE_LINK_SELECTOR
        )

        if locator.count() > 0:

            return locator.first

    except Exception:

        pass

    try:

        locator = page.get_by_role(
            "button",
            name=re.compile(
                r"^Create$",
                re.IGNORECASE
            )
        )

        if locator.count() > 0:

            return locator.first

    except Exception:

        pass

    return None


def construir_create_issue_url(base_url):

    parsed = urlsplit(
        str(base_url or "").strip()
    )

    if not parsed.scheme or not parsed.netloc:

        return str(base_url or "").strip()

    return f"{parsed.scheme}://{parsed.netloc}{CREATE_ISSUE_PATH}"


class JiraAutomationError(Exception):

    pass



def cargar_payload(path_argument):

    payload_path = Path(
        path_argument
    ).resolve()

    with open(
        payload_path,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )


def guardar_payload(path_argument, payload):
    payload_path = Path(
        path_argument
    ).resolve()

    with open(
        payload_path,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            payload,
            archivo,
            indent=4,
            ensure_ascii=False
        )


def cargar_state(path_text):

    path = Path(
        path_text
    )

    if not path.exists():

        return {
            "completed": {}
        }

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )


def guardar_state(path_text, state):

    path = Path(
        path_text
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            state,
            archivo,
            indent=4,
            ensure_ascii=False
        )


def resolver_referencias_issue(issue, completed):

    issue = dict(
        issue or {}
    )

    if issue.get("test_key_refs"):

        issue["test_keys"] = [
            completed.get(ref, {}).get("jira_key", "")
            for ref in issue.get("test_key_refs", [])
            if completed.get(ref, {}).get("jira_key")
        ]

    if issue.get("associated_test_key_refs"):

        issue["associated_test_keys"] = [
            completed.get(ref, {}).get("jira_key", "")
            for ref in issue.get("associated_test_key_refs", [])
            if completed.get(ref, {}).get("jira_key")
        ]

    if issue.get("associated_test_set_key_refs"):

        issue["associated_test_set_keys"] = [
            completed.get(ref, {}).get("jira_key", "")
            for ref in issue.get("associated_test_set_key_refs", [])
            if completed.get(ref, {}).get("jira_key")
        ]

    return issue


def ejecutar_step_issue(context, base_payload, issue):

    create_url = construir_create_issue_url(
        base_payload.get(
            "start_url",
            ""
        )
    )

    page = seleccionar_pagina_trabajo(
        context
    )
    print(f"Página controlada inicial: {page.url}")
    page.goto(
        create_url,
        wait_until="domcontentloaded",
        timeout=NAVIGATION_TIMEOUT_MS
    )
    page.wait_for_timeout(5000)
    print(f"Página tras goto Create Issue: {page.url}")

    esperar_login_si_hace_falta(
        page,
        create_url
    )
    print(f"Página antes de rellenar formulario: {page.url}")

    payload_step = {
        "project": base_payload.get("project", {}),
        "issue": issue
    }

    rellenar_formulario(
        page,
        payload_step
    )
    auto_submit_si_aplica(
        page,
        payload_step
    )

    return payload_step["issue"]


def ejecutar_workflow(context, payload):

    state_path = payload.get(
        "state_path",
        ""
    )
    state = cargar_state(
        state_path
    ) if state_path else {"completed": {}}
    completed = dict(
        state.get("completed", {})
    )

    for step in payload.get("workflow", []):

        step_id = step.get("id")

        if step_id and completed.get(step_id, {}).get("jira_key"):

            print(f"SKIP step ya creado -> {step_id}")
            continue

        issue = resolver_referencias_issue(
            step.get("issue", {}),
            completed
        )
        resultado = ejecutar_step_issue(
            context,
            payload,
            issue
        )

        jira_key = resultado.get("created_jira_key", "")
        jira_url = resultado.get("created_jira_url", "")

        if step_id and jira_key:

            completed[step_id] = {
                "jira_key": jira_key,
                "jira_url": jira_url,
                "type": resultado.get("type", "")
            }
            state["completed"] = completed

            if state_path:

                guardar_state(
                    state_path,
                    state
                )



def buscar_por_labels(page, labels):

    for label in labels:

        try:

            locator = page.get_by_label(
                re.compile(
                    rf"^{re.escape(label)}",
                    re.IGNORECASE
                )
            )

            if locator.count():

                return locator.first

        except Exception:

            continue

    return None


def buscar_picker_desde_labels(page, labels):

    for label in labels or []:

        try:

            selector_temporal = page.evaluate(
                """
                (labelText) => {
                    const normalize = (value) => String(value || '')
                        .normalize('NFD')
                        .replace(/[\u0300-\u036f]/g, '')
                        .trim()
                        .toLowerCase();

                    const isVisible = (element) => {
                        if (!element) {
                            return false;
                        }

                        const style = window.getComputedStyle(element);
                        const rect = element.getBoundingClientRect();
                        return style.visibility !== 'hidden'
                            && style.display !== 'none'
                            && rect.width > 0
                            && rect.height > 0;
                    };

                    const target = normalize(labelText);

                    if (!target) {
                        return null;
                    }

                    const candidates = Array.from(document.querySelectorAll(
                        'label, legend, [aria-label], [data-field-id]'
                    ));

                    const findFieldInContainer = (container) => {
                        if (!container) {
                            return null;
                        }

                        const field = container.querySelector(
                            '[role="combobox"], textarea, input:not([type="hidden"])'
                        );

                        return isVisible(field) ? field : null;
                    };

                    for (const candidate of candidates) {
                        const text = normalize(
                            candidate.textContent
                            || candidate.getAttribute('aria-label')
                            || candidate.getAttribute('data-field-id')
                        );

                        if (!text || (text !== target && !text.includes(target))) {
                            continue;
                        }

                        let field = null;

                        if (candidate.tagName === 'LABEL') {
                            const htmlFor = candidate.getAttribute('for');

                            if (htmlFor) {
                                field = document.getElementById(htmlFor);

                                if (isVisible(field)) {
                                    field.setAttribute('data-certflow-picker-probe', 'true');
                                    return '[data-certflow-picker-probe="true"]';
                                }
                            }
                        }

                        let container = candidate.parentElement;
                        let depth = 0;

                        while (!field && container && depth < 5) {
                            field = findFieldInContainer(container);
                            container = container.parentElement;
                            depth += 1;
                        }

                        if (field) {
                            field.setAttribute('data-certflow-picker-probe', 'true');
                            return '[data-certflow-picker-probe="true"]';
                        }
                    }

                    return null;
                }
                """,
                label
            )

            if not selector_temporal:

                continue

            locator = page.locator(
                str(selector_temporal)
            )

            if locator.count() > 0 and locator_es_visible(
                locator.first
            ):

                return locator.first

        except Exception:

            continue

        finally:

            try:

                page.locator(
                    "[data-certflow-picker-probe='true']"
                ).evaluate_all(
                    "elements => elements.forEach(element => element.removeAttribute('data-certflow-picker-probe'))"
                )

            except Exception:

                pass

    return None


def buscar_por_selectores(page, selectors):

    for selector in selectors or []:

        try:

            locator = page.locator(
                selector
            )

            if locator.count() > 0:

                return locator.first

        except Exception:

            continue

    return None


def buscar_visible_por_selectores(page, selectors):
    for selector in selectors or []:

        try:

            locator = page.locator(
                selector
            )
            total = min(
                locator.count(),
                10
            )

            for indice in range(total):

                candidato = locator.nth(
                    indice
                )

                if locator_es_visible(
                    candidato
                ):

                    return candidato

        except Exception:

            continue

    return None


def expandir_selectores_issue_picker(selectors):

    candidatos = []
    vistos = set()

    for selector in selectors or []:

        variantes = [
            selector
        ]
        match = re.search(
            r"(customfield_\d+)",
            str(selector or "")
        )

        if match:

            base = match.group(1)
            variantes.extend(
                [
                    f"#{base}",
                    f"#{base}-field",
                    f"#{base}-textarea",
                    f"input[id='{base}']",
                    f"textarea[id='{base}']",
                    f"input[name='{base}']",
                    f"textarea[name='{base}']",
                    f"input[id^='{base}']",
                    f"textarea[id^='{base}']",
                    f"input[name^='{base}']",
                    f"textarea[name^='{base}']",
                    f"[id^='{base}'][role='combobox']",
                    f"[name^='{base}'][role='combobox']",
                    f"[data-field-id='{base}'] input",
                    f"[data-field-id='{base}'] textarea",
                    f"[data-field-id='{base}'] [role='combobox']",
                    f"[aria-controls*='{base}']",
                    f"[aria-label*='{base}']"
                ]
            )

        for variante in variantes:

            limpio = str(
                variante or ""
            ).strip()

            if limpio and limpio not in vistos:

                vistos.add(
                    limpio
                )
                candidatos.append(
                    limpio
                )

    return candidatos



def buscar_combo(page, labels):

    for label in labels:

        try:

            locator = page.get_by_role(
                "combobox",
                name=re.compile(
                    label,
                    re.IGNORECASE
                )
            )

            if locator.count():

                for indice in range(locator.count()):

                    candidato = locator.nth(
                        indice
                    )

                    if locator_es_visible(
                        candidato
                    ):

                        return candidato

                return locator.first

        except Exception:

            continue

        locator = buscar_por_labels(
            page,
            [label]
        )

        if locator is not None:

            return locator

    return None


def locator_es_visible(locator):

    try:

        return locator.is_visible()

    except Exception:

        return False


def escribir_valor_en_input_oculto(locator, value):

    try:

        locator.evaluate(
            """
            (element, valor) => {
                element.value = valor;
                element.setAttribute('value', valor);
                element.dispatchEvent(new Event('input', { bubbles: true }));
                element.dispatchEvent(new Event('change', { bubbles: true }));
                element.dispatchEvent(new Event('blur', { bubbles: true }));
            }
            """,
            value
        )

        return True

    except Exception:

        return False



def completar_selector_autocomplete(page, labels, value):

    if not value:

        return False

    locator = buscar_combo(
        page,
        labels
    )

    if locator is None:

        return False

    if not locator_es_visible(
        locator
    ):

        print(f"SKIP combo oculto -> {labels[0]}")
        return False

    locator.click()
    locator.fill("")
    locator.type(
        value,
        delay=40
    )
    page.wait_for_timeout(1000)

    opcion = page.get_by_text(
        re.compile(
            re.escape(value),
            re.IGNORECASE
        )
    ).first

    try:

        opcion.click(timeout=5000)
        print(f"OK combo -> {labels[0]}")
        return True

    except Exception:

        try:

            locator.press("Enter")
            print(f"OK combo enter -> {labels[0]}")
            return True

        except Exception:

            print(f"SKIP combo sin opción -> {labels[0]}")

            return False


def completar_combobox_jira_por_id(
    page,
    selector,
    suggestion_container_id,
    value,
    field_name,
    alternate_values=None
):

    if not value:

        return False

    locator = buscar_por_selectores(
        page,
        [selector]
    )

    if locator is None or not locator_es_visible(locator):

        print(f"SKIP combo directo -> {field_name}")
        return False

    candidatos = [
        str(value).strip()
    ]

    for alternate in alternate_values or []:

        limpio = str(alternate or "").strip()

        if limpio and limpio not in candidatos:

            candidatos.append(limpio)

    for candidato in candidatos:

        try:

            locator.click()
            locator.press("Control+A")
            locator.fill("")
            locator.type(
                candidato,
                delay=35
            )
            page.wait_for_timeout(1200)

            suggestion = page.locator(
                f"#{suggestion_container_id}"
            ).get_by_text(
                re.compile(
                    re.escape(candidato),
                    re.IGNORECASE
                )
            ).first

            try:

                if suggestion.count() > 0 and suggestion.is_visible():

                    suggestion.click(timeout=3000)
                    page.wait_for_timeout(1200)

                    try:

                        valor_final = (locator.input_value() or "").strip()

                    except Exception:

                        valor_final = ""

                    if valor_final and candidato.lower() in valor_final.lower():

                        print(f"OK combo directo -> {field_name} ({valor_final})")
                        return True

            except Exception:

                pass

            try:

                locator.press("ArrowDown")
                locator.press("Enter")
                page.wait_for_timeout(1200)

                try:

                    valor_final = (locator.input_value() or "").strip()

                except Exception:

                    valor_final = ""

                if valor_final and candidato.lower() in valor_final.lower():

                    print(f"OK combo directo enter -> {field_name} ({valor_final})")
                    return True

            except Exception:

                continue

        except Exception:

            continue

    print(f"SKIP combo directo sin opción -> {field_name}")
    return False


def completar_test_repository_path(page, value):

    if not value:

        return False

    visible_picker = buscar_por_selectores(
        page,
        [
            "input[id^='test-repository-cf-picker-'][name^='test-repository-cf-picker-']"
        ]
    )

    if visible_picker is not None and locator_es_visible(
        visible_picker
    ):

        try:

            visible_picker.scroll_into_view_if_needed(timeout=4000)
            print("Pausa visual antes de abrir Test Repository Path...")
            page.wait_for_timeout(2500)
            visible_picker.click(timeout=4000, force=True)
            print("Picker abierto. Pausa visual...")
            page.wait_for_timeout(2500)

            segmentos = [
                segmento.strip()
                for segmento in re.split(r"[/>]", value)
                if segmento.strip()
            ]

            for indice_segmento, segmento in enumerate(segmentos):
                es_ultimo = indice_segmento == len(segmentos) - 1

                print(
                    f"{'Expandiendo' if not es_ultimo else 'Seleccionando'} carpeta: {segmento}"
                )

                accion_ok = bool(page.evaluate(
                    """
                    ({ folderTitle, expandOnly }) => {
                        const normalize = (value) => (value || '')
                            .normalize('NFD')
                            .replace(/[\u0300-\u036f]/g, '')
                            .trim()
                            .toLowerCase();

                        const target = normalize(folderTitle);
                        const nodes = Array.from(document.querySelectorAll('div.raven-folders-view-mode[title]'));
                        const titleNode = nodes.find(node => normalize(node.getAttribute('title')) === target);

                        if (!titleNode) {
                            return false;
                        }

                        titleNode.scrollIntoView({ block: 'center' });

                        const row = titleNode.closest('li.raven-folder-item');

                        if (expandOnly) {
                            if (row && String(row.getAttribute('expanded')).toLowerCase() === 'true') {
                                return true;
                            }

                            const spanId = titleNode.id || '';
                            let icon = null;

                            if (spanId.startsWith('span-')) {
                                icon = document.getElementById(`icon-${spanId.slice(5)}`);
                            }

                            if (!icon) {
                                icon = titleNode.querySelector('span[id^="icon-"]');
                            }

                            if (!icon) {
                                return false;
                            }

                            icon.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                            icon.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                            icon.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                            return true;
                        }

                        titleNode.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                        titleNode.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                        titleNode.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                        return true;
                    }
                    """,
                    {
                        "folderTitle": segmento,
                        "expandOnly": not es_ultimo
                    }
                ))

                if not accion_ok:

                    raise Exception(
                        f"No se pudo interactuar con segmento del repository path: {segmento}"
                    )

                page.wait_for_timeout(3200 if not es_ultimo else 2500)

            valor_final = ""

            try:

                valor_final = (visible_picker.input_value() or "").strip()

            except Exception:

                valor_final = ""

            if valor_final:

                print(f"OK picker -> Test Repository Path ({valor_final})")
                return True

        except Exception:

            pass

    return completar_input(
        page,
        [
            "Test Repository Path",
            "Test Repository path"
        ],
        value,
        allow_hidden=True,
        selectors=[
            "#customfield_14611"
        ]
    )



def completar_input(page, labels, value, allow_hidden=False, selectors=None):

    if not value:

        return False

    locator = None

    if selectors:

        locator = buscar_por_selectores(
            page,
            selectors
        )

    if locator is None:

        locator = buscar_por_labels(
            page,
            labels
        )

    if locator is None:

        return False

    if not locator_es_visible(
        locator
    ):

        if allow_hidden:

            if escribir_valor_en_input_oculto(
                locator,
                value
            ):

                print(f"OK hidden -> {labels[0]}")
                return True

        print(f"SKIP visible -> {labels[0]}")
        return False

    locator.click()

    try:

        locator.fill(value)

    except Exception:

        locator.press("Control+A")
        locator.type(
            value,
            delay=20
        )

    print(f"OK input -> {labels[0]}")

    return True


def completar_actions(page, value):

    if not value:

        return False

    abrir_tab_si_existe(
        page,
        "Test Details"
    )
    page.wait_for_timeout(1800)

    try:

        frame = page.frame_locator("iframe[id^='mce_']")
        body = frame.locator("body#tinymce")

        if body.count() > 0:

            body.click(timeout=4000)
            body.press("Control+A")
            body.fill("")
            body.type(
                value,
                delay=15
            )
            print("OK richtext -> Actions")
            return True

    except Exception:

        pass

    return completar_input(
        page,
        ["Actions"],
        value,
        selectors=[
            "textarea[id^='path-wiki_']",
            "textarea.wiki-editor-initialised",
            "textarea[israven='true']"
        ]
    )


def completar_labels(page, value):

    if not value:

        return False

    return completar_multi_issue_picker(
        page,
        [
            valor.strip()
            for valor in str(value).split(",")
            if valor.strip()
        ],
        "Labels",
        selectors=[
            "#labels-textarea",
            "textarea[role='combobox'][id='labels-textarea']",
            "input[aria-label='Labels']"
        ],
        labels=[
            "Labels"
        ]
    )


def completar_multi_issue_picker(
    page,
    issue_keys,
    log_name,
    selectors=None,
    labels=None
):

    valores = [
        str(valor).strip()
        for valor in issue_keys or []
        if str(valor).strip()
    ]

    if not valores:

        return False

    print(f"Buscando picker -> {log_name} ({len(valores)} valores)")

    locator = buscar_visible_por_selectores(
        page,
        expandir_selectores_issue_picker(
            selectors
        )
    )

    if locator is None and labels:

        locator = buscar_picker_desde_labels(
            page,
            labels
        )

    if locator is None and labels:

        locator = buscar_combo(
            page,
            labels
        )

    if locator is None and labels:

        candidato_label = buscar_por_labels(
            page,
            labels
        )

        if candidato_label is not None and locator_es_visible(
            candidato_label
        ):

            locator = candidato_label

    if locator is None:

        print(f"SKIP picker -> {log_name}")
        return False

    for valor in valores:

        locator.click(timeout=4000)
        try:

            locator.press("Control+A")
            locator.press("Backspace")

        except Exception:

            pass
        locator.type(
            valor,
            delay=20
        )
        page.wait_for_timeout(1200)

        opcion = page.get_by_text(
            re.compile(
                rf"^{re.escape(valor)}(?:\s|$)",
                re.IGNORECASE
            )
        ).first

        try:

            if opcion.count() > 0 and opcion.is_visible():

                opcion.click(timeout=4000)
                page.wait_for_timeout(800)
                continue

        except Exception:

            pass

        locator.press("Enter")
        page.wait_for_timeout(800)

    print(f"OK picker -> {log_name}")
    return True


def completar_typology_test_plan(page, typology_name):

    if not typology_name:

        return False

    locator = buscar_por_selectores(
        page,
        [
            "#customfield_25100",
            "select[name='customfield_25100']"
        ]
    )

    if locator is None:

        return False

    try:

        locator.select_option(label=typology_name)
        print("OK select -> Test Typology")
        return True

    except Exception:

        return False


def completar_fecha(page, selectors, value, log_name):

    ok = completar_input(
        page,
        [log_name],
        value,
        selectors=selectors
    )

    if ok:

        print(f"OK date -> {log_name}")

    return ok



def abrir_modal_create(page):

    locator = obtener_locator_create(
        page
    )

    if locator is None:

        raise JiraAutomationError(
            "No se encontró el control Create en Jira después del login."
        )

    try:

        href = locator.get_attribute(
            "href"
        ) or ""

        if "CreateIssue!default.jspa" in href:

            page.goto(
                page.url.split("/secure/")[0] + href,
                wait_until="domcontentloaded"
            )

            return

        locator.click(timeout=60000)
        return

    except Exception as error:

        raise JiraAutomationError(
            "No se pudo abrir el botón Create. Asegúrate de haber iniciado sesión en Jira y de que la página base sea correcta."
        ) from error


def create_disponible(page):

    locator = obtener_locator_create(
        page
    )

    if locator is None:

        return False

    return locator_es_visible(
        locator
    )


def formulario_create_disponible(page):

    locator = buscar_por_selectores(
        page,
        [
            "#project-field",
            "#issuetype-field",
            "#summary",
            "input[name='summary']",
            "textarea[name='description']"
        ]
    )

    if locator is None:

        return False

    return locator_es_visible(
        locator
    )


def esperar_formulario_create_listo(page):

    print("Esperando a que el formulario Create Issue quede listo...")

    page.wait_for_function(
        """
        () => {
            const summary = document.querySelector('#summary, input[name="summary"]');
            const description = document.querySelector('#description, textarea[name="description"]');
            return Boolean(summary && description);
        }
        """,
        timeout=FORM_READY_TIMEOUT_MS
    )

    page.wait_for_timeout(1500)
    print("Formulario Create Issue listo.")


def esperar_formulario_detalle_listo(page):

    print("Esperando campos de detalle...")

    page.wait_for_function(
        """
        () => {
            const summary = document.querySelector('#summary, input[name="summary"]');
            const description = document.querySelector('#description, textarea[name="description"]');
            return Boolean(summary || description);
        }
        """,
        timeout=30000
    )

    page.wait_for_timeout(1200)
    print("Campos de detalle listos.")


def avanzar_next_si_aplica(page):

    try:

        boton = page.locator(
            "#issue-create-submit"
        )

        if boton.count() == 0 or not boton.first.is_visible():

            return False

        texto = (boton.first.inner_text() or "").strip().lower()

        if texto != "next":

            return False

        boton.first.scroll_into_view_if_needed(timeout=5000)
        boton.first.click(timeout=5000, force=True)
        page.wait_for_timeout(2500)

        try:

            page.wait_for_function(
                """
                () => {
                    const summary = document.querySelector('#summary, input[name="summary"]');
                    const description = document.querySelector('#description, textarea[name="description"]');
                    return Boolean(summary || description);
                }
                """,
                timeout=3000
            )
            print("OK botón Next")
            return True

        except Exception:

            pass

        try:

            page.evaluate(
                """
                () => {
                    const form = document.querySelector('#issue-create');
                    if (form) {
                        form.requestSubmit();
                    }
                }
                """
            )
            page.wait_for_timeout(2500)
            page.wait_for_function(
                """
                () => {
                    const summary = document.querySelector('#summary, input[name="summary"]');
                    const description = document.querySelector('#description, textarea[name="description"]');
                    return Boolean(summary || description);
                }
                """,
                timeout=3000
            )
            print("OK submit Next")
            return True

        except Exception:

            print("SKIP botón Next sin efecto visible")
            return False

    except Exception:

        return False


def pagina_create_abierta(page):

    return "CreateIssue" in str(
        page.url or ""
    )


def login_pendiente(page):

    locator = buscar_por_selectores(
        page,
        [
            "input[type='password']",
            "input[name='password']",
            "input[name='os_username']",
            "input[type='email']"
        ]
    )

    if locator is None:

        return False

    return locator_es_visible(
        locator
    )

    try:

        return locator.is_visible()

    except Exception:

        return False


def esperar_login_si_hace_falta(page, create_url):

    if formulario_create_disponible(
        page
    ):

        return False

    if pagina_create_abierta(
        page
    ) and not login_pendiente(
        page
    ):

        print("Página Create Issue abierta sin login pendiente. Continuando...")
        return True

    print(
        "Esperando login o carga del formulario Create Issue. "
        "Si es la primera vez, inicia sesión manualmente en la ventana de Chrome abierta por Playwright. "
        "La automatización seguirá sola en cuanto Jira quede listo."
    )

    deadline = time.time() + LOGIN_WAIT_SECONDS
    create_reintentado = False

    while time.time() < deadline:

        page.wait_for_timeout(
            int(CREATE_POLL_SECONDS * 1000)
        )


        if formulario_create_disponible(
            page
        ):

            print("Formulario Create Issue detectado. Continuando...")
            return True

        if login_pendiente(
            page
        ):

            continue

        if pagina_create_abierta(
            page
        ):

            print("Página Create Issue abierta. Pasando al rellenado del formulario...")
            return True

        if not create_reintentado:

            try:

                print("Sesión detectada o página intermedia cargada. Navegando a Create Issue...")
                page.goto(
                    create_url,
                    wait_until="domcontentloaded",
                    timeout=NAVIGATION_TIMEOUT_MS
                )
                page.wait_for_timeout(4000)
                create_reintentado = True

            except Exception:

                create_reintentado = True
                continue

    raise JiraAutomationError(
        "No se detectó el formulario Create Issue después de esperar el login y la carga de Jira. Inicia sesión en la ventana de Playwright y vuelve a intentarlo."
    )



def abrir_tab_si_existe(page, tab_name):

    try:

        page.get_by_role(
            "tab",
            name=re.compile(
                rf"^{re.escape(tab_name)}$",
                re.IGNORECASE
            )
        ).click(timeout=4000)
        return True

    except Exception:

        return False



def rellenar_formulario(page, payload):

    project = payload.get(
        "project",
        {}
    )
    issue = payload.get(
        "issue",
        {}
    )
    issue_type = str(
        issue.get("type", "")
    ).strip()

    print("Completando Project...")
    project_ok = completar_combobox_jira_por_id(
        page,
        "#project-field",
        "project-suggestions",
        project.get("key") or project.get("name"),
        "Project",
        alternate_values=[
            project.get("name"),
            project.get("key")
        ]
    )

    if not project_ok:

        project_ok = completar_selector_autocomplete(
            page,
            ["Project"],
            project.get("key") or project.get("name")
        )

    if not project_ok:

        print("Project quedó sin cambios automáticos; se asume que Jira ya lo fijó o el combo visible no fue usable.")

    print("Completando Issue Type...")
    issue_type_ok = completar_combobox_jira_por_id(
        page,
        "#issuetype-field",
        "issuetype-suggestions",
        issue.get("type"),
        "Issue Type"
    )

    if not issue_type_ok:

        issue_type_ok = completar_selector_autocomplete(
            page,
            ["Issue Type", "Issue type"],
            issue.get("type")
        )

    if not issue_type_ok:

        print("Issue Type quedó sin cambios automáticos; se asume que Jira ya lo fijó o el combo visible no fue usable.")

    avanzar_next_si_aplica(
        page
    )

    esperar_formulario_detalle_listo(
        page
    )

    print("Completando Summary...")
    completar_input(
        page,
        ["Summary"],
        issue.get("summary"),
        selectors=[
            "#summary",
            "input[name='summary']",
            "input[aria-label='Summary']"
        ]
    )

    print("Completando Description...")
    completar_input(
        page,
        ["Description"],
        issue.get("description"),
        selectors=[
            "#description",
            "textarea[name='description']",
            "textarea[data-projectkey]"
        ]
    )

    if issue_type == "Test Set":

        abrir_tab_si_existe(
            page,
            "Tests"
        )
        page.wait_for_timeout(1200)
        completar_multi_issue_picker(
            page,
            issue.get("test_keys", []),
            "Tests del Test Set",
            selectors=[
                "#customfield_14612-textarea"
            ],
            labels=[
                "Tests"
            ]
        )

    if issue_type == "Test Plan":

        completar_typology_test_plan(
            page,
            issue.get("typology_name")
        )

        detalles_tab_abierta = abrir_tab_si_existe(
            page,
            "Tests Plan Details"
        )
        if not detalles_tab_abierta:

            abrir_tab_si_existe(
                page,
                "Tests"
            )
        page.wait_for_timeout(1200)

        completar_fecha(
            page,
            [
                "#customfield_11307",
                "input[name='customfield_11307']"
            ],
            issue.get("end_date"),
            "End Date"
        )
        completar_fecha(
            page,
            [
                "#customfield_14617",
                "input[name='customfield_14617']"
            ],
            issue.get("begin_date"),
            "Begin Date"
        )
        try:

            page.keyboard.press("Tab")

        except Exception:

            pass

        page.wait_for_timeout(500)
        page.wait_for_timeout(1500)
        associated_test_set_keys = issue.get(
            "associated_test_set_keys",
            []
        )

        associated_test_keys = issue.get(
            "associated_test_keys",
            []
        )

        if associated_test_set_keys:

            print(
                "Intentando asociar Test Sets al Test Plan: "
                f"{', '.join(associated_test_set_keys)}"
            )

            if not completar_multi_issue_picker(
                page,
                associated_test_set_keys,
                "Test Sets asociados al Test Plan",
                selectors=[
                    "#customfield_14627-textarea",
                    "#customfield_14628-textarea",
                    "#customfield_14625-textarea"
                ],
                labels=[
                    "Associated Test Sets",
                    "Test Sets",
                    "Test Set"
                ]
            ):

                raise JiraAutomationError(
                    "No se pudieron asociar los Test Set al Test Plan."
                )

        elif associated_test_keys:

            if not completar_multi_issue_picker(
                page,
                associated_test_keys,
                "Tests asociados al Test Plan",
                selectors=[
                    "#customfield_14626-textarea"
                ],
                labels=[
                    "Associated Tests",
                    "Tests"
                ]
            ):

                raise JiraAutomationError(
                    "No se pudieron asociar los Tests al Test Plan."
                )

    labels = issue.get("labels")

    if labels:

        abrir_tab_si_existe(
            page,
            "General"
        )
        page.wait_for_timeout(800)
        print("Completando Labels...")
        completar_labels(
            page,
            labels
        )

    print("Completando Actions...")
    completar_actions(
        page,
        issue.get("actions")
    )

    repository_path = issue.get(
        "repository_path"
    )

    if repository_path:

        abrir_tab_si_existe(
            page,
            "General"
        )

        print("Completando Test Repository Path...")
        completar_test_repository_path(
            page,
            repository_path
        )



def auto_submit_si_aplica(page, payload):

    issue = payload.get(
        "issue",
        {}
    )

    if not issue.get("auto_submit"):

        print("Formulario Jira listo para revisión manual del usuario.")
        return

    page.get_by_role(
        "button",
        name=re.compile(
            r"^Create$",
            re.IGNORECASE
        )
    ).last.click(timeout=5000)
    page.wait_for_timeout(4000)

    issue_key = extraer_issue_key_desde_url(
        page.url
    )

    if issue_key:

        issue["created_jira_key"] = issue_key
        issue["created_jira_url"] = page.url
        print(f"OK created -> {issue_key}")


def liberar_lock_automation():

    try:

        if LOCK_PATH.exists():

            LOCK_PATH.unlink()

    except Exception:

        pass


def seleccionar_pagina_trabajo(context):

    paginas = list(
        context.pages
    )

    for page in paginas:

        url_actual = str(
            page.url or ""
        ).strip()

        if "CreateIssue" in url_actual or "jira.globaldevtools.bbva.com" in url_actual:

            try:

                page.bring_to_front()

            except Exception:

                pass

            return page

    if paginas:

        page = paginas[0]

        try:

            page.bring_to_front()

        except Exception:

            pass

        return page

    raise JiraAutomationError(
        "No se encontró ninguna pestaña disponible en el navegador de Playwright. Cierra ventanas previas de automatización y vuelve a intentarlo."
    )



def ejecutar(payload):

    try:

        from playwright.sync_api import sync_playwright

    except ImportError as error:

        raise JiraAutomationError(
            "Playwright no está instalado. Ejecuta: pip install -r requirements.txt y luego python -m playwright install chrome"
        ) from error

    PLAYWRIGHT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )
    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    start_url = str(
        payload.get(
            "start_url",
            ""
        ) or ""
    ).strip()

    if not start_url:

        raise JiraAutomationError(
            "El payload no contiene start_url para abrir Jira."
        )

    create_url = construir_create_issue_url(
        start_url
    )

    with sync_playwright() as playwright:

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            channel=payload.get(
                "browser_channel",
                "chrome"
            ),
            args=[
                "--start-maximized"
            ],
            no_viewport=True
        )
        context.set_default_timeout(
            NAVIGATION_TIMEOUT_MS
        )
        context.set_default_navigation_timeout(
            NAVIGATION_TIMEOUT_MS
        )

        try:

            if payload.get("workflow"):

                ejecutar_workflow(
                    context,
                    payload
                )

            else:

                page = seleccionar_pagina_trabajo(
                    context
                )
                print(f"Página controlada inicial: {page.url}")
                page.goto(
                    create_url,
                    wait_until="domcontentloaded",
                    timeout=NAVIGATION_TIMEOUT_MS
                )
                page.wait_for_timeout(5000)
                print(f"Página tras goto Create Issue: {page.url}")

                esperar_login_si_hace_falta(
                    page,
                    create_url
                )
                print(f"Página antes de rellenar formulario: {page.url}")

                rellenar_formulario(
                    page,
                    payload
                )
                auto_submit_si_aplica(
                    page,
                    payload
                )

            print("Automatización Jira lanzada correctamente.")
            print("Cierra la ventana del navegador cuando termines para finalizar el proceso asistido.")
            context.wait_for_event(
                "close",
                timeout=0
            )
            liberar_lock_automation()

        except Exception:

            try:

                page.screenshot(
                    path=str(SCREENSHOT_PATH),
                    full_page=True
                )
                print(f"Se guardó screenshot de error en: {SCREENSHOT_PATH}")

            except Exception:

                pass

            print("La ventana de Chrome se mantendrá abierta para inspección manual. Ciérrala cuando termines.")

            try:

                context.wait_for_event(
                    "close",
                    timeout=0
                )
                liberar_lock_automation()

            except Exception:

                pass

            raise



def main():

    if len(sys.argv) < 2:

        raise JiraAutomationError(
            "Uso: python scripts/run_jira_playwright.py <payload.json>"
        )

    payload_path = sys.argv[1]
    payload = cargar_payload(
        payload_path
    )
    ejecutar(
        payload
    )
    guardar_payload(
        payload_path,
        payload
    )


if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        print(f"[Jira Playwright] Error: {error}")
        raise
