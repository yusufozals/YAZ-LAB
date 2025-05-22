import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import json

# Ana proje dizinini Python path'ine ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.data_generator import DroneDataGenerator


def ensure_dir_exists(dir_path):
    """Dizinin var olduğundan emin ol, yoksa oluştur"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"{dir_path} dizini oluşturuldu.")


def create_standard_test_scenarios():
    """Proje dökümantasyonunda belirtilen standart test senaryolarını oluştur"""
    print("Standart test senaryoları oluşturuluyor...")

    test_data_dir = "../src/visualizations/data/generated_data/"
    ensure_dir_exists(test_data_dir)

    # Senaryo 1: 5 drone, 20 teslimat, 2 no-fly zone
    print("Senaryo 1 oluşturuluyor: 5 drone, 20 teslimat, 2 no-fly zone")
    scenario1 = DroneDataGenerator(
        num_drones=5,
        num_delivery_points=20,
        num_no_fly_zones=2,
        area_size=(1000, 1000),
        seed=42  # Tekrarlanabilir sonuçlar için sabit tohum değeri
    )

    scenario1.generate_all_data()
    scenario1.save_to_file(f"{test_data_dir}scenario1.json")
    scenario1.visualize(save_fig=True, filename=f"{test_data_dir}scenario1_visualization.png")

    # Senaryo 2: 10 drone, 50 teslimat, 5 dinamik no-fly zone
    print("Senaryo 2 oluşturuluyor: 10 drone, 50 teslimat, 5 no-fly zone")
    scenario2 = DroneDataGenerator(
        num_drones=10,
        num_delivery_points=50,
        num_no_fly_zones=5,
        area_size=(2000, 2000),
        seed=43
    )

    scenario2.generate_all_data()
    scenario2.save_to_file(f"{test_data_dir}scenario2.json")
    scenario2.visualize(save_fig=True, filename=f"{test_data_dir}scenario2_visualization.png")

    print("Standart test senaryoları başarıyla oluşturuldu.")


def create_edge_case_scenarios():
    """Algoritmanın sınırlarını test etmek için uç durum senaryoları oluştur"""
    print("Uç durum senaryoları oluşturuluyor...")

    test_data_dir = "../src/visualizations/data/generated_data/"
    ensure_dir_exists(test_data_dir)

    # Yüksek Yoğunluklu Senaryo: Çok sayıda NFZ ve teslimat noktası
    print("Yüksek yoğunluklu senaryo oluşturuluyor: 15 drone, 100 teslimat, 10 no-fly zone")
    high_density = DroneDataGenerator(
        num_drones=15,
        num_delivery_points=100,
        num_no_fly_zones=10,
        area_size=(2500, 2500),
        seed=44
    )

    high_density.generate_all_data()
    high_density.save_to_file(f"{test_data_dir}high_density_scenario.json")
    high_density.visualize(save_fig=True, filename=f"{test_data_dir}high_density_visualization.png")

    # NFZ Yoğunluklu Senaryo: Çok sayıda uçuş yasağı bölgesi
    print("NFZ yoğun senaryo oluşturuluyor: 5 drone, 20 teslimat, 15 no-fly zone")
    many_nfz = DroneDataGenerator(
        num_drones=5,
        num_delivery_points=20,
        num_no_fly_zones=15,
        area_size=(1200, 1200),
        seed=45
    )

    many_nfz.generate_all_data()
    many_nfz.save_to_file(f"{test_data_dir}many_nfz_scenario.json")
    many_nfz.visualize(save_fig=True, filename=f"{test_data_dir}many_nfz_visualization.png")

    # Sınırlı Kapasite Senaryosu: Düşük kapasiteli drone'lar ve ağır paketler
    print("Sınırlı kapasite senaryosu oluşturuluyor...")

    # Özel DroneDataGenerator sınıfı
    class LimitedCapacityGenerator(DroneDataGenerator):
        def generate_drones(self):
            """Daha düşük kapasiteli drone'lar oluştur"""
            drones = super().generate_drones()
            # Tüm drone'ların taşıma kapasitesini azalt
            for drone in drones:
                drone["max_weight"] = round(drone["max_weight"] * 0.6, 2)  # %60 taşıma kapasitesi
                drone["battery"] = int(drone["battery"] * 0.7)  # %70 batarya kapasitesi
            return drones

        def generate_delivery_points(self):
            """Daha ağır paketler oluştur"""
            delivery_points = super().generate_delivery_points()
            # Bazı paketleri daha ağır yap
            for dp in delivery_points:
                if np.random.random() < 0.3:  # %30 olasılıkla
                    dp["weight"] = round(min(dp["weight"] * 2.5, 15.0), 2)  # Daha ağır paketler
            return delivery_points

    limited_capacity = LimitedCapacityGenerator(
        num_drones=8,
        num_delivery_points=40,
        num_no_fly_zones=5,
        area_size=(1500, 1500),
        seed=46
    )

    limited_capacity.generate_all_data()
    limited_capacity.save_to_file(f"{test_data_dir}limited_capacity_scenario.json")
    limited_capacity.visualize(save_fig=True, filename=f"{test_data_dir}limited_capacity_visualization.png")

    # Dar Zaman Aralığı Senaryosu: Sıkışık teslimat zamanları
    print("Dar zaman aralığı senaryosu oluşturuluyor...")

    class TightTimeWindowGenerator(DroneDataGenerator):
        def generate_delivery_points(self):
            """Dar zaman aralıklı teslimatlar oluştur"""
            delivery_points = super().generate_delivery_points()
            # Zaman aralıklarını sıkılaştır
            for dp in delivery_points:
                # Mevcut zaman aralığını parse et
                start_str, end_str = dp["time_window"]
                start_hour, start_min = map(int, start_str.split(':'))
                end_hour, end_min = map(int, end_str.split(':'))

                # Zaman aralığını daralt (örn. 2 saat yerine 30-60 dk)
                new_end_hour = start_hour
                new_end_min = start_min + np.random.randint(30, 61)  # 30-60 dk arası

                # Dakika taşması durumunda saat arttır
                if new_end_min >= 60:
                    new_end_hour += 1
                    new_end_min -= 60

                # Yeni zaman aralığını ayarla
                dp["time_window"] = (
                    f"{start_hour:02d}:{start_min:02d}",
                    f"{new_end_hour:02d}:{new_end_min:02d}"
                )

                # Bazı teslimatların önceliğini yükselt
                if np.random.random() < 0.4:  # %40 olasılıkla
                    dp["priority"] = 5  # En yüksek öncelik

            return delivery_points

    tight_time = TightTimeWindowGenerator(
        num_drones=10,
        num_delivery_points=30,
        num_no_fly_zones=4,
        area_size=(1800, 1800),
        seed=47
    )

    tight_time.generate_all_data()
    tight_time.save_to_file(f"{test_data_dir}tight_time_scenario.json")
    tight_time.visualize(save_fig=True, filename=f"{test_data_dir}tight_time_visualization.png")

    print("Uç durum senaryoları başarıyla oluşturuldu.")


def create_custom_scenario():
    """Özel test senaryosu oluştur"""
    print("Özel test senaryosu oluşturuluyor...")

    test_data_dir = "../src/visualizations/data/generated_data/"
    ensure_dir_exists(test_data_dir)

    # Karma bir senaryo
    custom = DroneDataGenerator(
        num_drones=7,
        num_delivery_points=35,
        num_no_fly_zones=6,
        area_size=(1500, 1500),
        seed=48
    )

    data = custom.generate_all_data()

    # Özel düzenlemeler yap
    # 1. Belirli bir bölgeye yüksek öncelikli teslimatlar ekle
    target_area = (500, 500, 800, 800)  # (x_min, y_min, x_max, y_max)
    for dp in data["delivery_points"]:
        x, y = dp["pos"]
        if (target_area[0] <= x <= target_area[2] and
                target_area[1] <= y <= target_area[3]):
            dp["priority"] = 5  # En yüksek öncelik

    # 2. Drone filonun yarısını yüksek kapasiteli yap
    num_high_capacity = len(data["drones"]) // 2
    for i in range(num_high_capacity):
        data["drones"][i]["max_weight"] = 15.0
        data["drones"][i]["battery"] = 15000

    custom.save_to_file(f"{test_data_dir}custom_scenario.json")
    custom.visualize(save_fig=True, filename=f"{test_data_dir}custom_visualization.png")

    # Ayrıca düzenlenmiş veriyi manuel olarak kaydet
    with open(f"{test_data_dir}custom_scenario_modified.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print("Özel test senaryosu başarıyla oluşturuldu.")


def generate_all_test_data():
    """Tüm test verilerini oluştur"""
    print("Test veri seti oluşturma işlemi başlatılıyor...")

    # Ana dizinleri kontrol et
    ensure_dir_exists("../src/visualizations/data")
    ensure_dir_exists("../src/visualizations/output")
    ensure_dir_exists("../src/visualizations/output/routes")
    ensure_dir_exists("../src/visualizations/output/visualizations")

    # Test senaryolarını oluştur
    create_standard_test_scenarios()
    create_edge_case_scenarios()
    create_custom_scenario()

    print("\nTüm test verileri başarıyla oluşturuldu.")
    print("Test senaryoları 'data/generated_data/' dizinine kaydedildi.")
    print("Görselleştirmeler de aynı dizinde bulunabilir.")


if __name__ == "__main__":
    generate_all_test_data()