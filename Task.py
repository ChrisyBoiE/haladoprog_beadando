import pandas as pd
import numpy as np
from scipy import stats
from google.colab import drive

# Google Drive csatlakoztatása
drive.mount('/content/drive')

# Saját függvény az adatok beolvasására
def egyedi_csv_beolvasas(filepath):
    with open(filepath, 'r') as file:
        sorok = file.readlines()
    
    # Az oszlopnevek beolvasása
    oszlopok = sorok[0].strip().split(',')
    
    # Az adatok beolvasása
    adatok = []
    for sor in sorok[1:]:
        # Az egyes sorok feldolgozása
        reszek = []
        aktualis_resz = ''
        idezojelben = False
        for karakter in sor:
            if karakter == '"' and not idezojelben:
                idezojelben = True
            elif karakter == '"' and idezojelben:
                idezojelben = False
            elif karakter == ',' and not idezojelben:
                reszek.append(aktualis_resz.strip())
                aktualis_resz = ''
            else:
                aktualis_resz += karakter
        reszek.append(aktualis_resz.strip())
        
        if len(reszek) == len(oszlopok):
            adatok.append(reszek)
        else:
            print(f"Hiba a sor feldolgozása során: {sor}")
    
    # Adatkeret létrehozása
    df = pd.DataFrame(adatok, columns=oszlopok)
    
    # Hiányzó értékek kezelése
    df.replace(['NA', 'N/A', 'NULL', ''], np.nan, inplace=True)
    
    return df

# Az adatok betöltése és előfeldolgozása
fajl_utvonal = '/content/drive/MyDrive/beadandok/haladoprogramozas/credit_card_transaction_flow.csv'
adatok = egyedi_csv_beolvasas(fajl_utvonal)

# Ellenőrizzük az oszlopokat és az első néhány sort
#print("\nAz adatok oszlopai:")
#print(adatok.columns)
#print("\nAz adatok első néhány sora:")
#print(adatok.head())

# Debug: Az első 20 sor kiírása
print("\nAz első 20 sor részletes kiírása:")
for index, sor in adatok.head(20).iterrows():
    sor_adatok = ', '.join([f"{oszlop}: {sor[oszlop]}" for oszlop in adatok.columns])
    print(sor_adatok)

# Eredeti adatok másolása az összehasonlításhoz
eredeti_adatok = adatok.copy()

# 1. Eredeti adatok mérete
print(f"Eredeti adatok mérete: {adatok.shape}")

# 3. 'Transaction Amount' oszlop előkészítése
# Eltávolítjuk a '$' jelet és átalakítjuk az értékeket float típusra
adatok['Transaction Amount'] = adatok['Transaction Amount'].replace('[\$,]', '', regex=True).astype(float)

# 4. Hiányzó értékek interpolálása a 'Transaction Amount' oszlopban
# Lineáris interpolációval pótoljuk a hiányzó értékeket, majd az átlaggal töltjük ki a maradék hiányzó értékeket
adatok['Transaction Amount'] = adatok['Transaction Amount'].interpolate(method='linear')
adatok['Transaction Amount'] = adatok['Transaction Amount'].fillna(adatok['Transaction Amount'].mean())
print("\nAdatok mérete az interpoláció után:", adatok.shape)

# 5. Duplikált tranzakciók eltávolítása
kezdeti_sorok_szama = len(adatok)
adatok.drop_duplicates(inplace=True)
vegso_sorok_szama = len(adatok)
print(f"\nAdatok mérete a duplikált sorok eltávolítása után: {adatok.shape}")
print(f"Eltávolított duplikált sorok száma: {kezdeti_sorok_szama - vegso_sorok_szama}")

# 6. Formázási hibák javítása
# A 'Transaction Amount' oszlopot numerikus típusra alakítjuk, a 'Date' oszlopot pedig dátum típusra
adatok['Transaction Amount'] = pd.to_numeric(adatok['Transaction Amount'], errors='coerce')
adatok['Date'] = pd.to_datetime(adatok['Date'], errors='coerce', format='%d-%m-%Y')

# Újraellenőrizzük a hiányzó értékeket
print("\nHiányzó értékek száma a formázási hibák után:")
hianyzo_ertekek_szama = {oszlop: 0 for oszlop in adatok.columns}
for index, sor in adatok.iterrows():
    for oszlop in adatok.columns:
        if pd.isnull(sor[oszlop]):
            hianyzo_ertekek_szama[oszlop] += 1
print(hianyzo_ertekek_szama)

# Hiányzó értékek részletes megjelenítése
print("\nHiányzó értékek részletes megjelenítése:")
print(adatok[adatok.isnull().any(axis=1)])

# A hiányzó értékeket kitöltjük, hogy ne maradjanak üres értékek
adatok['Transaction Amount'] = adatok['Transaction Amount'].fillna(adatok['Transaction Amount'].mean())
adatok['Date'] = adatok['Date'].ffill()
print("\nAdatok mérete a formázási hibák utáni kitöltés után:", adatok.shape)

# 7. Anomáliák felismerése és kezelése
# Kiugró értékek korlátozása a 99. percentilisre (nem eltávolítás, csak limitálás)
percentilis_99 = adatok['Transaction Amount'].quantile(0.99)
adatok['Transaction Amount'] = np.where(adatok['Transaction Amount'] > percentilis_99, percentilis_99, adatok['Transaction Amount'])
print("\nKiugró értékek limitálva a 99. percentilisre")

# 8. Adatok aggregálása napi, heti és havi szintre
adatok['Date'] = pd.to_datetime(adatok['Date'])

# Napi aggregálás
napi_adatok = adatok.groupby(adatok['Date'].dt.date).agg({'Transaction Amount': 'sum'}).reset_index()
napi_adatok.columns = ['Date', 'Total Transaction Amount']

# Heti aggregálás
heti_adatok = adatok.groupby(adatok['Date'].dt.to_period('W')).agg({'Transaction Amount': 'sum'}).reset_index()
heti_adatok.columns = ['Week', 'Total Transaction Amount']

# Havi aggregálás
havi_adatok = adatok.groupby(adatok['Date'].dt.to_period('M')).agg({'Transaction Amount': 'sum'}).reset_index()
havi_adatok.columns = ['Month', 'Total Transaction Amount']

# 9. Az eredmény exportálása
# A tisztított adatokat és az aggregált adatokat exportáljuk CSV formátumban
tisztitott_fajl_utvonal = '/content/drive/MyDrive/beadandok/haladoprogramozas/cleaned_transactions.csv'
napi_aggregalt_fajl_utvonal = '/content/drive/MyDrive/beadandok/haladoprogramozas/daily_aggregated_transactions.csv'
heti_aggregalt_fajl_utvonal = '/content/drive/MyDrive/beadandok/haladoprogramozas/weekly_aggregated_transactions.csv'
havi_aggregalt_fajl_utvonal = '/content/drive/MyDrive/beadandok/haladoprogramozas/monthly_aggregated_transactions.csv'

adatok.to_csv(tisztitott_fajl_utvonal, index=False)
napi_adatok.to_csv(napi_aggregalt_fajl_utvonal, index=False)
heti_adatok.to_csv(heti_aggregalt_fajl_utvonal, index=False)
havi_adatok.to_csv(havi_aggregalt_fajl_utvonal, index=False)

# 10. Jelentés az adattisztítási folyamatról
print("\nAdattisztítási folyamat jelentése:")
print(f"Hiányzó értékek interpolálása és kitöltése befejezve.")
print(f"Formátumhibák javítva.")
print(f"Kiugró értékek limitálva a 99. percentilisre.")
print("Az adatok sikeresen aggregálva napi, heti és havi szintre és exportálva.")
# Ellenőrizzük, hogy az eredeti adatokat nem módosítottuk
if eredeti_adatok.equals(adatok):
    print("\nHiba: Az eredeti adatokat módosítottuk!")
else:
    print("\nAz eredeti adatokat módosítottuk.")
