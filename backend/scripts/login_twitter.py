import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# File to store session cookies and localStorage
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "twitter_state.json")

async def main():
    print("="*60)
    print(" TWITTER MANUAL LOGIN SCRIPT (ANTI-BOT BYPASS)")
    print("="*60)
    print("1. Sebuah browser Chromium akan terbuka.")
    print("2. Silakan login ke Twitter/X secara MANUAL (isi email, password, dll).")
    print("3. Selesaikan CAPTCHA atau verifikasi email jika diminta.")
    print("4. Setelah berhasil login dan masuk ke Beranda (Timeline),")
    print("   script ini akan MENYIMPAN session Anda dan menutup browser.")
    print("="*60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--start-maximized"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        await page.goto("https://x.com/login")
        
        print("\n⏳ Menunggu Anda login... (script otomatis menunggu hingga Anda di Home)")
        try:
            # Tunggu sampai URL berubah menjadi /home (indikasi login sukses)
            await page.wait_for_url("**/home", timeout=300000) # Timeout 5 menit
            print("\n✅ Berhasil masuk ke Home!")
            
            # Simpan state (cookies, localStorage)
            await context.storage_state(path=STATE_FILE)
            print(f"✅ Session berhasil disimpan ke: {STATE_FILE}")
            print("🚀 Anda sekarang bisa menjalankan pipeline Celery tanpa terblokir!")
        except Exception as e:
            print(f"\n❌ Gagal atau waktu habis (5 menit): {e}")
            print("Silakan jalankan ulang script ini jika belum selesai login.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
