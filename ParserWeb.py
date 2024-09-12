import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from TextSpan import TextSpanPDF
from selenium.common.exceptions import StaleElementReferenceException


class ParserWeb:
    def __init__(self):
        self.list_spans = []

    def parse_webpage(self, url):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--start-maximized")
        service = Service('C:/chr-drv/chromedriver.exe')
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        driver.execute_script(r"""
            function wrapTextNodesInSpan(element) {
                element.childNodes.forEach(child => {
                    if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== '') {
                        const parts = child.textContent.split(/(\s+|[.,!?;:"(){}\[\]])/);
                        const spanElements = parts.map(part => {
                            if (part.trim() !== '') {
                                return `<span class="word">${part}</span>`;
                            } else {
                                return part;
                            }
                        }).join('');
                        const spanContainer = document.createElement('span');
                        spanContainer.innerHTML = spanElements;
                        element.replaceChild(spanContainer, child);
                    } else if (child.nodeType === Node.ELEMENT_NODE) {
                        wrapTextNodesInSpan(child);
                    }
                });
            }

            wrapTextNodesInSpan(document.body);
        """)

        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "word"))
        )

        for elem in elements:
            try:
                text = elem.text.strip()

                # Фільтрація тексту з атрибутами, як src=, href=, або URL
                if text and len(text) > 1 and not re.match(r'^[\s.,!?;:"(){}\[\]<>/]+$', text):
                    # Фільтрація за наявністю "src=" або URL
                    if '=' in text or '<' in text or '>' in text or '/' in text or re.search(r'http[s]?://', text):
                        continue  # Пропускаємо ці елементи

                    text = text.rstrip(".,!?;:\"(){}[]")
                    style = self.get_style_properties(driver, elem)
                    font_size = self.extract_font_size(style.get("fontSize", ""))
                    font_family = self.get_active_font_family(driver, elem)
                    color = style.get("color", "black")
                    x1, y1, x2, y2 = self.get_element_coordinates(driver, elem)
                    word_span = TextSpanPDF()
                    text = text.lower()
                    word_span.set_text(text)
                    word_span.set_size_text(font_size)
                    word_span.set_background_color("")
                    word_span.set_color_text(color)
                    word_span.set_coords(x1, y1, x2, y2)
                    word_span.set_flags("")
                    self.list_spans.append(word_span)

                    print(f"Text: {text}, Font Family: {font_family}")

            except StaleElementReferenceException:
                continue

        driver.quit()
        return self.list_spans


    def get_style_properties(self, driver, element):
        script = r"""
        const elem = arguments[0];
        const style = window.getComputedStyle(elem);
        return {
            fontSize: style.fontSize,
            fontWeight: style.fontWeight,
            fontStyle: style.fontStyle,
            color: style.color,
            fontFamily: style.fontFamily
        };
        """
        return driver.execute_script(script, element)

    def get_active_font_family(self, driver, element):
        script = r"""
        const elem = arguments[0];
        const style = window.getComputedStyle(elem);
        const fontFamilyList = style.fontFamily.split(',');
        for (const font of fontFamilyList) {
            const fontName = font.trim().replace(/['"]/g, ''); 
            if (document.fonts.check(`1em ${fontName}`)) {
                return fontName;
            }
        }
        return style.fontFamily.split(',')[0].trim().replace(/['"]/g, ''); 
        """
        return driver.execute_script(script, element)

    def extract_font_size(self, font_size_str):
        match = re.match(r"(\d+(\.\d+)?)px", font_size_str)
        if match:
            return float(match.group(1))
        return None

    def extract_font_weight(self, font_weight_str):
        try:
            weight = int(font_weight_str)
            if weight == 400:
                return "normal"
            elif weight == 700:
                return "bold"
            else:
                return str(weight)
        except ValueError:
            return font_weight_str

    def get_element_coordinates(self, driver, element):
        script = r"""
        const rect = arguments[0].getBoundingClientRect();
        return [rect.left, rect.top, rect.right, rect.bottom];
        """
        return driver.execute_script(script, element)
