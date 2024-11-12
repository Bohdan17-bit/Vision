import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, JavascriptException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from TextSpan import TextSpanPDF

class ParserWeb:
    def __init__(self):
        self.list_spans = []

    def parse_webpage(self, url):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-software-rasterizer")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)

        # Оновлений JavaScript для обгортання тільки видимих текстових вузлів
        driver.execute_script(r"""
            function wrapTextNodesInSpan(element) {
                const ignoredTags = ['SCRIPT', 'STYLE', 'NOSCRIPT', 'IMG', 'IFRAME'];
                const hiddenStyles = ['none', 'hidden', 'collapse', 'transparent'];

                element.childNodes.forEach(child => {
                    const style = window.getComputedStyle(element);
                    const isHidden = hiddenStyles.includes(style.display) || hiddenStyles.includes(style.visibility) || parseFloat(style.opacity) === 0;

                    if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== '' && !isHidden) {
                        const parts = child.textContent.split(/(\s+|[.,!?;:"(){}\[\]])/);
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

        elements = driver.find_elements(By.CLASS_NAME, "word")

        for elem in elements:
            try:
                text = elem.text.strip()
                # Фільтрація: видаляємо елементи, що містять URL або специфічні символи
                if text and re.match(r'^[a-zA-Zа-яА-ЯіїєґІЇЄҐ0-9]+$', text):  # Додаємо підтримку чисел (0-9)
                    text = self.clean_html_tags(text)
                    text = text.rstrip(".,!?;:\"(){}[]<>")

                    style = self.get_style_properties(driver, elem)
                    font_size = self.extract_font_size(style.get("fontSize", "12px"))
                    font_family = self.get_active_font_family(driver, elem)
                    color = style.get("color", "black")
                    x1, y1, x2, y2 = self.get_element_coordinates(driver, elem)

                    word_span = TextSpanPDF()
                    text = text.lower()
                    word_span.set_text(text)
                    word_span.set_size_text(int(font_size))
                    word_span.set_background_color("")
                    word_span.set_color_text(color)
                    word_span.set_coords(x1, y1, x2, y2)
                    word_span.set_flags("")
                    self.list_spans.append(word_span)

                    print(f"Text: {text}")

            except (StaleElementReferenceException, JavascriptException) as e:
                print(f"Exception caught: {e}, skipping this element")
                continue

        driver.quit()
        return self.list_spans

    def clean_html_tags(self, text):
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def get_active_font_family(self, driver, element):
        try:
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
        except JavascriptException:
            return "default"

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
                 fontFamily: style.fontFamily || "default"
             };
             """
            return driver.execute_script(script, element)
        except JavascriptException:
            return {"fontSize": "12px", "fontWeight": "normal", "fontStyle": "normal", "color": "black",
                    "fontFamily": "default"}

    def extract_font_size(self, font_size_str):
        match = re.match(r"(\d+(\.\d+)?)px", font_size_str)
        if match:
            return float(match.group(1))
        return 12.0

    def get_element_coordinates(self, driver, element):
        try:
            script = r"""
             const rect = arguments[0].getBoundingClientRect();
             return [rect.left, rect.top, rect.right, rect.bottom];
             """
            return driver.execute_script(script, element)
        except JavascriptException:
            return [0, 0, 0, 0]
