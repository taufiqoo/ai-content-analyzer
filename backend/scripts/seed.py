"""
Seed default niche configs.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import NicheConfig

sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(sync_url)
Session = sessionmaker(bind=engine)


DEFAULT_NICHES = [
    {
        "name": "Self-Development",
        "keywords": ["produktivitas", "mindset", "kebiasaan", "buku", "sukses", "motivasi", "self-improvement"],
        "hook_formulas": [
            "Jangan bilang lo udah dewasa kalo masih X",
            "Ini kesalahan self-development yang bikin lo stuck — dan lo nggak sadar ngelakuinnya",
            "Semua orang SALAH soal produktivitas",
        ],
        "script_rules": "Fokus pada insight counter-intuitive. Gunakan contoh sehari-hari yang relatable. Target audiens 18-30 tahun.",
        "target_duration_seconds": 60,
    },
    {
        "name": "Finance & Investing",
        "keywords": ["investasi", "saham", "bitcoin", "keuangan", "passive income", "ekonomi", "tabungan"],
        "hook_formulas": [
            "[Figur/Institusi besar] baru aja [aksi besar] — dan alasannya bikin gue takut untuk [X]",
            "Stop investasi, kalo duit lo masih kurang dari 30 juta, sini gue jelasin",
            "Semua orang SALAH soal cara nabung",
        ],
        "script_rules": "Gunakan analogi sederhana untuk konsep keuangan. Hindari jargon teknis tanpa penjelasan. Sertakan contoh angka yang konkret.",
        "target_duration_seconds": 75,
    },
    {
        "name": "Geopolitik & Ekonomi Global",
        "keywords": ["geopolitik", "perang", "ekonomi global", "bitcoin", "dolar", "krisis", "sistem keuangan"],
        "hook_formulas": [
            "Para pemimpin dunia baru aja ngumumin sesuatu yang seharusnya bikin semua orang panik",
            "Ada yang lagi terjadi sekarang — dan hampir nggak ada yang ngomongin ini di Indonesia",
            "Bentar — [figur/institusi] baru aja [aksi] yang seharusnya bikin lo khawatir",
        ],
        "script_rules": "Tone netral, mengundang diskusi. Sertakan konteks yang mudah dipahami orang awam. Gunakan analogi untuk konsep geopolitik.",
        "target_duration_seconds": 90,
    },
    {
        "name": "Relationship & Psikologi",
        "keywords": ["hubungan", "pasangan", "komunikasi", "psikologi", "mindset", "self-love"],
        "hook_formulas": [
            "Ngaku deh — lo pernah ngerasain X",
            "Jangan heran kenapa hubungan lo sering berantem — karena ada satu hal yang belum lo tau",
            "Ini alasan kenapa pasangan lo sering salah paham sama lo",
        ],
        "script_rules": "Empatik dan relatable. Hindari menghakimi. Gunakan contoh situasi spesifik yang sering terjadi.",
        "target_duration_seconds": 60,
    },
    {
        "name": "Tech & AI",
        "keywords": ["AI", "teknologi", "startup", "digital", "programming", "masa depan", "otomasi"],
        "hook_formulas": [
            "Dunia lagi balik — dan kebanyakan orang nggak nyadar",
            "GILA. Kenapa nggak ada yang bilang dari dulu kalo AI bisa X",
            "Ada peluang yang lagi gede banget sekarang — dan hampir nggak ada yang ngomongin ini",
        ],
        "script_rules": "Gunakan bahasa awam, bukan bahasa teknis. Gunakan analogi untuk menjelaskan teknologi. Fokus pada dampak ke kehidupan sehari-hari.",
        "target_duration_seconds": 60,
    },
]


def seed():
    db = Session()
    try:
        count = db.query(NicheConfig).count()
        if count > 0:
            print(f"[Seed] Already seeded ({count} niches found). Skipping.")
            return

        for data in DEFAULT_NICHES:
            niche = NicheConfig(**data)
            db.add(niche)

        db.commit()
        print(f"[Seed] ✅ Seeded {len(DEFAULT_NICHES)} niche configs.")
    except Exception as e:
        db.rollback()
        print(f"[Seed] Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
