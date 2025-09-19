from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
import os


@task
def order_robots_from_RobotSpareBin():
    """
    Solicita robots a RobotSpareBin Industries Inc.
    Guarda el recibo del pedido en formato PDF.
    Guarda la captura de pantalla del robot solicitado.
    Inserta la captura de pantalla del robot en el recibo PDF.
    Crea un archivo ZIP con los recibos generados.
    """

    os.makedirs("output/receipts", exist_ok=True)
    os.makedirs("output/screenshots", exist_ok=True)

    open_robot_order_website()
    orders = get_orders()

    for row in orders:
        close_annoying_modal()
        fill_the_form(row)
        preview_robot()
        submit_order()

        order_number = row["Order number"]
        pdf_file = store_receipt_as_pdf(order_number)
        screenshot = screenshot_robot(order_number)
        embed_screenshot_to_receipt(screenshot, pdf_file)

        page = browser.page()
        page.click("#order-another")

    archive_receipts()


def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def get_orders():
    http = HTTP()
    http.download(
        url="https://robotsparebinindustries.com/orders.csv",
        target_file="orders.csv",
        overwrite=True
    )
    tables = Tables()
    orders = tables.read_table_from_csv("orders.csv", header=True)
    return orders


def close_annoying_modal():
    page = browser.page()
    if page.is_visible("button.btn-warning"):
        page.click("button.btn-warning")


def fill_the_form(order):
    page = browser.page()
    page.select_option("#head", order["Head"])
    page.click(f'input[name="body"][value="{order["Body"]}"]')
    page.fill("input[placeholder='Enter the part number for the legs']", order["Legs"])
    page.fill("#address", order["Address"])


def preview_robot():
    page = browser.page()
    page.click("#preview")


def submit_order():
    page = browser.page()
    attempts = 0
    while attempts < 5:
        page.click("#order")
        if page.is_visible("#receipt"):
            return True
        attempts += 1
        print(f"Error al enviar, reintentando... ({attempts})")
    raise Exception("No se pudo completar el pedido después de varios intentos.")


def store_receipt_as_pdf(order_number):
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf_file = f"output/receipts/receipt_{order_number}.pdf"
    pdf.html_to_pdf(receipt_html, pdf_file)
    return pdf_file


def screenshot_robot(order_number):
    page = browser.page()
    screenshot_file = f"output/screenshots/robot_{order_number}.png"
    page.locator("#robot-preview-image").screenshot(path=screenshot_file)
    return screenshot_file


def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()
    pdf.add_watermark_image_to_pdf(
        image_path=screenshot,
        source_path=pdf_file,
        output_path=pdf_file
    )


def archive_receipts():
    archive = Archive()
    archive.archive_folder_with_zip(
        folder="output/receipts",
        archive_name="output/receipts.zip"
    )
    return "output/receipts.zip"












