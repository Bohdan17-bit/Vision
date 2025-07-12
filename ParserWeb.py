import logging
import re
import requests
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, JavascriptException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from TextSpan import TextSpanPDF

logging.basicConfig(
    level=logging.DEBUG,
    filename='parser_logs.txt',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ParserWeb:
    def __init__(self):
        self.list_spans = []
        self.body_font_family = "Times New Roman"

    def parse_webpage(self, url):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-software-rasterizer")

        logging.info(f"Opening URL: {url}")
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
        except Exception as e:
            logging.error(f"Error while initializing the web driver or opening the URL: {e}")
            return []

        css_styles = self.parse_css_files(driver, url)
        default_font = self.extract_font_from_css_styles(css_styles)
        self.body_font_family = default_font

        try:
            driver.execute_script(r"""
                function wrapTextNodesInSpan(element) {
                    const ignoredTags = ['SCRIPT', 'STYLE', 'NOSCRIPT', 'IMG', 'IFRAME'];
                    const hiddenStyles = ['none', 'hidden', 'collapse', 'transparent'];

                    element.childNodes.forEach(child => {
                        const style = window.getComputedStyle(element);
                        const isHidden = hiddenStyles.includes(style.display) || hiddenStyles.includes(style.visibility) || parseFloat(style.opacity) === 0;

                        if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== '' && !isHidden) {
                            const parts = child.textContent.split(/(\s+)/);
                            const spanContainer = document.createElement('span');
                            parts.forEach(part => {
                                if (part.trim() !== '') {
                                    const spanElement = document.createElement('span');
                                    spanElement.classList.add('word');
                                    spanElement.textContent = part;
                                    spanContainer.appendChild(spanElement);
                                } else {
                                    const textNode = document.createTextNode(part);
                                    spanContainer.appendChild(textNode);
                                }
                            });
                            element.replaceChild(spanContainer, child);
                        } else if (child.nodeType === Node.ELEMENT_NODE && !ignoredTags.includes(child.tagName) && !isHidden) {
                            wrapTextNodesInSpan(child);
                        }
                    });
                }
                wrapTextNodesInSpan(document.body);
            """)
        except JavascriptException as e:
            logging.error(f"JavaScript execution error: {e}")

        elements = driver.find_elements(By.CLASS_NAME, "word")
        previous_coords = None

        for elem in elements:
            try:
                text = elem.text.strip()

                if not text or all(char in {'.', ',', '-', ' ', '<', '>', '!', '?', "'", "’"} for char in text):
                    continue

                text = re.sub(r'[“”"«»„\'’]', ' ', text).strip()
                text = re.sub(r'[\[\]]', '', text)
                text = text.replace('_', '-')
                text = re.sub(r'\s+', ' ', text)
                split_text = [part for part in re.split(r'[.,\-<>\s!?]+', text) if part]

                for part in split_text:
                    if re.match(r'^[a-zA-Zа-яА-ЯіїєґІЇЄҐ0-9©]+$', part):
                        style = self.get_style_properties(driver, elem)
                        font_size = self.extract_font_size(style.get("fontSize", "12px"))

                        font_family = self.get_active_font_family(driver, elem)
                        if not font_family:
                            font_family = default_font or "Times New Roman"

                        word_span = TextSpanPDF()
                        word_span.set_font(font_family)
                        word_span.set_text(part)
                        word_span.set_size_text(int(font_size))
                        word_span.set_color_text(style.get("color", "black"))
                        word_span.set_background_color("")
                        word_span.set_flags("")

                        x1, y1, x2, y2 = self.get_element_coordinates(driver, elem)
                        word_span.set_coords(x1, y1, x2, y2)

                        if previous_coords:
                            distance = self.get_distance_to_next_element(previous_coords, (x1, y1))
                            word_span.distance_to_next_span = distance

                        self.list_spans.append(word_span)
                        previous_coords = (x2, y2)

                        logging.debug(
                            f"Processed text: {part}, Font: {font_family}, Size: {font_size}, "
                            f"Distance to next: {getattr(word_span, 'distance_to_next_span', 'N/A')}"
                        )

            except (StaleElementReferenceException, JavascriptException) as e:
                logging.error(f"{type(e).__name__} caught: {e}, skipping this element")
                continue
            except Exception as e:
                logging.error(f"Unexpected error caught: {e}, skipping this element")
                continue

        driver.quit()
        logging.info("Finished parsing webpage.")
        return self.list_spans

    def get_active_font_family(self, driver, element):
        try:
            script = r"""
            const elem = arguments[0];
            const style = window.getComputedStyle(elem);
            const fontFamily = style.fontFamily || '';
            const fontList = fontFamily.split(',').map(f => f.trim().replace(/['"]/g, ''));
            for (const font of fontList) {
                if (font && font.toLowerCase() !== 'sans-serif' && font.toLowerCase() !== 'serif' && font.toLowerCase() !== 'monospace') {
                    return font;
                }
            }
            return 'Times New Roman';
            """
            return driver.execute_script(script, element)
        except JavascriptException:
            return "Times New Roman"

    def get_style_properties(self, driver, element):
        try:
            script = r"""
            const elem = arguments[0];
            const style = window.getComputedStyle(elem);
            return {
                fontSize: style.fontSize || "12px",
                fontWeight: style.fontWeight || "normal",
                fontStyle: style.fontStyle || "normal",
                color: style.color || "black",
                fontFamily: style.fontFamily || "Times New Roman"
            };
            """
            return driver.execute_script(script, element)
        except JavascriptException:
            return {
                "fontSize": "12px",
                "fontWeight": "normal",
                "fontStyle": "normal",
                "color": "black",
                "fontFamily": "Times New Roman"
            }

    def extract_font_size(self, font_size_str):
        match = re.match(r"(\d+(\.\d+)?)px", font_size_str)
        return float(match.group(1)) if match else 12.0

    def get_element_coordinates(self, driver, element):
        try:
            script = r"""
            const rect = arguments[0].getBoundingClientRect();
            return [rect.left, rect.top, rect.right, rect.bottom];
            """
            return driver.execute_script(script, element)
        except JavascriptException:
            return [0, 0, 0, 0]

    def get_distance_to_next_element(self, prev_coords, curr_coords):
        prev_x, prev_y = prev_coords
        curr_x, curr_y = curr_coords
        return ((curr_x - prev_x) ** 2 + (curr_y - prev_y) ** 2) ** 0.5

    def parse_css_files(self, driver, base_url):
        css_styles = {}
        try:
            links = driver.find_elements(By.TAG_NAME, 'link')
            for link in links:
                rel = link.get_attribute('rel')
                href = link.get_attribute('href')
                if rel and 'stylesheet' in rel.lower() and href:
                    full_url = urljoin(base_url, href)
                    response = requests.get(full_url)
                    if response.status_code == 200:
                        css_text = response.text
                        matches = re.findall(r'([.#]?[\w\-]+)\s*{([^}]*font[^}]*)}', css_text)
                        for selector, styles in matches:
                            properties = {}
                            for line in styles.split(';'):
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    properties[key.strip()] = value.strip()
                            css_styles[selector.strip('.#')] = properties
        except Exception as e:
            logging.warning(f"Could not fetch or parse CSS: {e}")
        return css_styles

    def extract_font_from_css_styles(self, css_styles):
        if "body" in css_styles:
            font = css_styles["body"].get("font")
            if font:
                font_list = re.findall(r'"[^"]+"|[\w\-]+', font)
                for f in font_list:
                    f = f.strip('"').strip()
                    if f.lower() not in ['sans-serif', 'serif', 'monospace']:
                        return f
        return "Times New Roman"
