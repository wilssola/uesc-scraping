import os
import json
import base64

from firebase_admin import initialize_app
from firebase_admin import credentials
from firebase_admin import firestore

from time import sleep
from requests import post

from dotenv import load_dotenv

from playwright.sync_api import sync_playwright
from playwright_recaptcha import recaptchav2


k_url = 'https://www.prograd.uesc.br/PortalSagres/'
k_hours = 6

def init_firebase_app():
    firebase_sdk_base64 = os.getenv('FIREBASE_SDK_BASE64')
    print(firebase_sdk_base64, '\n')

    firebase_sdk_json = json.loads(base64.b64decode(firebase_sdk_base64))
    print(firebase_sdk_json, '\n')

    credential = credentials.Certificate(firebase_sdk_json)
    print(credential, '\n')

    return initialize_app(credential=credential, options=None, name=os.getenv('FIREBASE_APP_NAME'))

def get_firestore_db(app):
    return firestore.client(app)

def sagres_scraping(db):
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(k_url)

        sleep(1)
        with recaptchav2.SyncSolver(page) as solver:
            token = solver.solve_recaptcha(wait=True)
            print(token, '\n')

        sleep(2)
        page.get_by_label('Usuário:').fill(os.getenv('UESC_SCRAPING_USER'))

        sleep(3)
        page.get_by_label('Senha:').fill(os.getenv('UESC_SCRAPING_PASSWORD'))

        sleep(1)
        page.get_by_text('Entrar').click()

        sleep(10)

        for recado_classe in page.query_selector_all('.recado-classe'):
            recado_text = recado_classe.inner_text()
            print(recado_text, '\n')

            recado_hash = str(hash(recado_text))
            print(recado_hash, '\n')

            data = recado_text.encode(encoding='utf-8')

            sleep(1)

            recado_ref = db.collection('sagres').document(os.getenv('UESC_SCRAPING_USER')).collection('recados').document(recado_hash)

            recado_doc = recado_ref.get()
            if recado_doc.exists:
                continue

            recado_ref.create({ 'text': recado_text, 'hash': recado_hash })

            post('https://ntfy.sh/' + os.getenv('NTFY_TOPIC'), data)

        browser.close()

    sleep(k_hours * 3600)
    main()

def main():
    load_dotenv()

    app = init_firebase_app()
    db = get_firestore_db(app)

    sagres_scraping(db)


if __name__ == '__main__':
    main()