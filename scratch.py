import argparse
import asyncio
from playwright.async_api import async_playwright

class TempMailCLI:
    def __init__(self):
        self.browser = None
        self.page = None
        self.email = None

    async def start_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        await self.page.goto('https://temp-mail.org/en/')
        print("waiting for selector")
        await self.page.wait_for_selector('button#click-to-refresh', timeout=30000)

    async def close_browser(self):
        await self.browser.close()
        await self.playwright.stop()

    async def generate_email(self):
        await self.page.wait_for_selector('input#mail')
        email_element = await self.page.query_selector('input#mail')
        self.email = await email_element.input_value()
        print(f"Generated Email: {self.email}")

    async def refresh_inbox(self):
        await self.page.click('button#click-to-refresh')
        await self.page.wait_for_timeout(5000)
        messages = await self.page.evaluate('''() => {
            let emails = [];
            document.querySelectorAll('.inbox-dataList ul li').forEach(email => {
                emails.push({
                    from: email.querySelector('.from').innerText,
                    subject: email.querySelector('.subject').innerText,
                    time: email.querySelector('.time').innerText,
                });
            });
            return emails;
        }''')
        if messages:
            for message in messages:
                print(f"From: {message['from']}, Subject: {message['subject']}, Time: {message['time']}")
        else:
            print("No new messages")

    async def view_email(self, index):
        await self.page.click(f'.inbox-dataList ul li:nth-child({index+1})')
        await self.page.wait_for_selector('.inbox-data-content-intro', timeout=30000)
        content = await self.page.inner_text('.inbox-data-content-intro')
        print(f"Email Content:\n{content}")

    async def run(self, command, index=None):
        await self.start_browser()
        if command == 'generate':
            await self.generate_email()
        elif command == 'refresh':
            await self.refresh_inbox()
        elif command == 'view' and index is not None:
            await self.view_email(index)
        await self.close_browser()

def main():
    parser = argparse.ArgumentParser(description="Temp Mail CLI")
    parser.add_argument('command', choices=['generate', 'refresh', 'view'], help='Command to execute')
    parser.add_argument('--index', type=int, help='Index of the email to view (used with view command)')
    args = parser.parse_args()

    cli = TempMailCLI()
    asyncio.run(cli.run(args.command, args.index))

if __name__ == '__main__':
    main()
