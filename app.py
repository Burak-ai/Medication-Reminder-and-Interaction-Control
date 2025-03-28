from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# Kullanıcıların ilaçlarını saklamak için bellek içi veri yapısı
kullanici_ilaclari = {}

# Genişletilmiş ilaç etkileşim veritabanı (Türkçe versiyon)
ilac_etkilesimleri = {
    ('Warfarin', 'Aspirin'): {
        'uyari': 'Bu iki ilacın birlikte kullanılması kanama riskini artırabilir.',
        'seviyesi': 'yüksek',
        'oneriler': 'Doktorunuza danışmadan birlikte kullanmayınız.'
    },
    ('Lisinopril', 'İbuprofen'): {
        'uyari': 'İbuprofen, Lisinopril’in tansiyon düşürücü etkisini azaltabilir ve böbrek sorunlarına yol açabilir.',
        'seviyesi': 'orta',
        'oneriler': 'Sık kullanımdan kaçının ve doktorunuza danışın.'
    },
    ('Simvastatin', 'Greyfurt Suyu'): {
        'uyari': 'Greyfurt suyu, Simvastatin’in kandaki seviyesini artırarak yan etki riskini yükseltebilir.',
        'seviyesi': 'orta',
        'oneriler': 'Greyfurt tüketiminden kaçının.'
    },
    ('Metformin', 'Cimetidin'): {
        'uyari': 'Cimetidin, Metformin’in kandaki seviyesini artırarak yan etki riskini yükseltebilir.',
        'seviyesi': 'düşük',
        'oneriler': 'Kan şekeri seviyenizi takip ediniz.'
    },
    ('Nitrogliserin', 'Sildenafil'): {
        'uyari': 'Bu iki ilaç bir arada kullanılırsa ciddi tansiyon düşüklüğüne neden olabilir.',
        'seviyesi': 'yüksek',
        'oneriler': 'Kesinlikle birlikte kullanmayınız, alternatif tedavi seçenekleri için doktorunuza danışınız.'
    },
    ('ACE İnhibitörleri', 'Potasyum Takviyeleri'): {
        'uyari': 'Potasyum seviyesinin tehlikeli derecede yükselmesine neden olabilir.',
        'seviyesi': 'orta',
        'oneriler': 'Kan potasyum seviyenizi düzenli olarak kontrol ettiriniz.'
    },
    ('Parasetamol', 'Alkol'): {
        'uyari': 'Alkol ile birlikte kullanımı karaciğer hasarına yol açabilir.',
        'seviyesi': 'yüksek',
        'oneriler': 'Alkol tüketiminden kaçının.'
    },
    ('Aspirin', 'Klopidogrel'): {
        'uyari': 'Bu ilaçlar birlikte kullanıldığında kanama riskini artırabilir.',
        'seviyesi': 'yüksek',
        'oneriler': 'Yakın takiple kullanınız.'
    },
    ('Metoprolol', 'Verapamil'): {
        'uyari': 'Kalp hızı ve kan basıncı aşırı derecede düşebilir.',
        'seviyesi': 'yüksek',
        'oneriler': 'Eş zamanlı kullanımını doktorunuza danışın.'
    },
    ('Digoksin', 'Furosemid'): {
        'uyari': 'Düşük potasyum seviyelerine bağlı olarak digoksin toksisitesi riski artabilir.',
        'seviyesi': 'orta',
        'oneriler': 'Elektrolit seviyenizi düzenli kontrol ettirin.'
    },
    ('Levotiroksin', 'Demir Takviyeleri'): {
        'uyari': 'Demir, Levotiroksin emilimini azaltabilir.',
        'seviyesi': 'düşük',
        'oneriler': 'İki ilaç arasına zaman bırakın.'
    },
    ('Antibiyotikler', 'Doğum Kontrol Hapları'): {
        'uyari': 'Antibiyotikler doğum kontrol haplarının etkinliğini azaltabilir.',
        'seviyesi': 'orta',
        'oneriler': 'Ek önlemler kullanınız.'
    },
    ('Allopurinol', 'Azatioprin'): {
        'uyari': 'Birlikte kullanım toksisite riskini artırabilir.',
        'seviyesi': 'yüksek',
        'oneriler': 'Doktor kontrolü altında kullanınız.'
    },
    ('Simetidin', 'Teofilin'): {
        'uyari': 'Simetidin, Teofilin’in yan etkilerini artırabilir.',
        'seviyesi': 'orta',
        'oneriler': 'Düzenli doz takibi yapınız.'
    },
    ('Antikoagülanlar', 'NSAIDler'): {
        'uyari': 'Kanama riski önemli ölçüde artabilir.',
        'seviyesi': 'yüksek',
        'oneriler': 'Birlikte kullanımdan kaçının.'
    },
    ('Diltiazem', 'Beta Blokerler'): {
        'uyari': 'Aşırı kalp hızı ve kan basıncı düşüşü riski.',
        'seviyesi': 'orta',
        'oneriler': 'Doktor kontrolünde kullanın.'
    },
    ('İnsülin', 'Tiazid Diüretikler'): {
        'uyari': 'Kan şekeri kontrolü zorlaşabilir.',
        'seviyesi': 'orta',
        'oneriler': 'Kan şekeri seviyenizi düzenli kontrol edin.'
    },
    ('Fenitoin', 'Doğum Kontrol Hapları'): {
        'uyari': 'Doğum kontrol haplarının etkinliği azalabilir.',
        'seviyesi': 'orta',
        'oneriler': 'Alternatif korunma yöntemleri kullanınız.'
    },
    ('Antasitler', 'Levotiroksin'): {
        'uyari': 'Antasitler Levotiroksin emilimini azaltabilir.',
        'seviyesi': 'düşük',
        'oneriler': 'Zaman aralığı bırakın.'
    },
    ('Diüretikler', 'Lityum'): {
        'uyari': 'Lityum toksisitesi riski artabilir.',
        'seviyesi': 'yüksek',
        'oneriler': 'Serum seviyenizi düzenli kontrol ettirin.'
    },
    ('Efedrin', 'Monoamin Oksidaz İnhibitörleri'): {
        'uyari': 'Ciddi hipertansiyon riski.',
        'seviyesi': 'yüksek',
        'oneriler': 'Kesinlikle birlikte kullanmayınız.'
    }
}


def etkilesim_kontrol(ilac1, ilac2):
    """
    İki ilaç arasındaki etkileşimi kontrol eder.
    """
    anahtar = (ilac1, ilac2)
    if anahtar in ilac_etkilesimleri:
        return ilac_etkilesimleri[anahtar]
    anahtar = (ilac2, ilac1)
    return ilac_etkilesimleri.get(anahtar)

def tum_etkilesimleri_kontrol_et(ilaclar):
    """
    Kullanıcının ilaçları arasındaki tüm olası etkileşimleri kontrol eder.
    """
    uyarilar = []
    n = len(ilaclar)
    for i in range(n):
        for j in range(i + 1, n):
            ilac1 = ilaclar[i]['ilac']
            ilac2 = ilaclar[j]['ilac']
            etkilesim = etkilesim_kontrol(ilac1, ilac2)
            if etkilesim:
                uyarilar.append({
                    'ilaclar': (ilac1, ilac2),
                    'uyari': etkilesim['uyari'],
                    'seviyesi': etkilesim['seviyesi'],
                    'oneriler': etkilesim['oneriler']
                })
    return uyarilar

def ai_optimize_zaman(kullanici_rutini, ilac_zamani):
    """
    Kullanıcının ilaç alma zamanlarını optimize eder.
    (Bu fonksiyon şu an basit bir versiyon, ileride geliştirilebilir.)
    """
    return ilac_zamani

def hatirlatma_gonder(kullanici_id, ilac):
    """Kullanıcıya hatırlatma gönderir """
    print(f"📢 Kullanıcı {kullanici_id}: {ilac['ilac']} ilacınızı almayı unutmayın! (Doz: {ilac.get('doz', 'Bilinmiyor')})")

def hatirlatma_zamanlayici(kullanici_id):
    """
    Kullanıcının ilaç saatlerini takip eder ve zamanı geldiğinde hatırlatma yapar.
    """
    def zamanlayici_dongu():
        while True:
            su_an = datetime.now()
            ilaclar = kullanici_ilaclari.get(kullanici_id, [])
            for ilac in ilaclar:
                hatirlatma_saati = ilac['zaman']
                if su_an <= hatirlatma_saati < su_an + timedelta(minutes=1):
                    hatirlatma_gonder(kullanici_id, ilac)
            time.sleep(60)  # 1 dakika sonra tekrar kontrol et

    t = threading.Thread(target=zamanlayici_dongu, daemon=True)
    t.start()

@app.route('/ilac_ekle', methods=['POST'])
def ilac_ekle():
    """
    Kullanıcının ilaçlarını ekleyebileceği endpoint.
    """
    veri = request.get_json()
    kullanici_id = veri.get('kullanici_id')
    ilac = veri.get('ilac')
    doz = veri.get('doz')
    zaman_str = veri.get('zaman')
    kullanici_rutini = veri.get('kullanici_rutini', {})

    try:
        hatirlatma_saati = datetime.fromisoformat(zaman_str)
    except Exception:
        return jsonify({"hata": "Geçersiz zaman formatı. ISO formatı kullanınız."}), 400

    optimize_edilmis_zaman = ai_optimize_zaman(kullanici_rutini, hatirlatma_saati)

    yeni_ilac = {
        'ilac': ilac,
        'doz': doz,
        'zaman': optimize_edilmis_zaman
    }

    if kullanici_id in kullanici_ilaclari:
        kullanici_ilaclari[kullanici_id].append(yeni_ilac)
    else:
        kullanici_ilaclari[kullanici_id] = [yeni_ilac]
        hatirlatma_zamanlayici(kullanici_id)

    etkilesimler = tum_etkilesimleri_kontrol_et(kullanici_ilaclari[kullanici_id])
    return jsonify({
        "mesaj": "İlaç başarıyla eklendi.",
        "optimize_edilmis_zaman": optimize_edilmis_zaman.isoformat(),
        "etkilesim_uyarilari": etkilesimler
    })

@app.route('/ilaclar', methods=['GET'])
def ilaclari_getir():
    """
    Belirli bir kullanıcının ilaçlarını getirir.
    """
    kullanici_id = request.args.get('kullanici_id')
    ilaclar = kullanici_ilaclari.get(kullanici_id, [])
    for ilac in ilaclar:
        ilac['zaman'] = ilac['zaman'].isoformat()
    return jsonify(ilaclar)

@app.route('/etkilesim_kontrol', methods=['POST'])
def etkilesim_kontrolu():
    """
    Gönderilen ilaç listesindeki etkileşimleri kontrol eder.
    """
    veri = request.get_json()
    ilaclar = veri.get('ilaclar', [])
    etkilesimler = tum_etkilesimleri_kontrol_et(ilaclar)
    return jsonify(etkilesimler)

@app.route('/')
def index():
    """Sunucunun çalıştığını kontrol etmek için basit bir sayfa."""
    return "📢 İlaç Hatırlatma ve Etkileşim Kontrol Uygulaması Çalışıyor!"

if __name__ == '__main__':
    app.run(debug=True)
