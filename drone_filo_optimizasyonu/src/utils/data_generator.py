import numpy as np
import random
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime, timedelta
import json
import os


class DroneDataGenerator:
    def __init__(self,
                 num_drones=5,
                 num_delivery_points=20,
                 num_no_fly_zones=2,
                 area_size=(1000, 1000),  # metre cinsinden x, y
                 seed=None):
        """
        Drone filo optimizasyonu için veri üreteci

        Parametreler:
        -------------
        num_drones : int
            Oluşturulacak drone sayısı
        num_delivery_points : int
            Oluşturulacak teslimat noktası sayısı
        num_no_fly_zones : int
            Oluşturulacak uçuş yasağı bölgesi sayısı
        area_size : tuple
            Çalışma alanının boyutları (metre cinsinden)
        seed : int
            Rastgele sayı üreteci için tohum değeri
        """
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        self.num_drones = num_drones
        self.num_delivery_points = num_delivery_points
        self.num_no_fly_zones = num_no_fly_zones
        self.area_size = area_size

        # Merkez depo konumu
        self.depot_position = (area_size[0] // 2, area_size[1] // 2)

        # Veri yapıları
        self.drones = []
        self.delivery_points = []
        self.no_fly_zones = []

    def generate_drones(self):
        """Drone'ları oluştur"""
        self.drones = []

        # Farklı drone tipleri için özellikler
        drone_types = [
            {"max_weight": 5.0, "battery": 5000, "speed": 10.0},  # Küçük drone
            {"max_weight": 10.0, "battery": 8000, "speed": 8.0},  # Orta drone
            {"max_weight": 15.0, "battery": 12000, "speed": 6.0}  # Büyük drone
        ]

        for i in range(self.num_drones):
            # Rastgele bir drone tipi seç
            drone_type = random.choice(drone_types)

            # Varyasyon ekle
            max_weight = max(1.0, np.random.normal(drone_type["max_weight"], 1.0))
            battery = int(max(2000, np.random.normal(drone_type["battery"], 500)))
            speed = max(5.0, np.random.normal(drone_type["speed"], 1.0))

            # Hepsinin başlangıç noktası depo
            start_pos = self.depot_position

            drone = {
                "id": i,
                "max_weight": round(max_weight, 2),
                "battery": battery,
                "speed": round(speed, 2),
                "start_pos": start_pos
            }

            self.drones.append(drone)

        return self.drones

    def generate_delivery_points(self):
        """Teslimat noktalarını oluştur"""
        self.delivery_points = []

        # Rastgele saat aralığı üretmek için başlangıç saati
        start_hour = 9  # 09:00

        for i in range(self.num_delivery_points):
            # Rastgele konum (depoya çok yakın olmamasını sağla)
            while True:
                pos_x = np.random.uniform(0, self.area_size[0])
                pos_y = np.random.uniform(0, self.area_size[1])

                # Depodan uzaklık kontrolü
                dist_to_depot = ((pos_x - self.depot_position[0]) ** 2 +
                                 (pos_y - self.depot_position[1]) ** 2) ** 0.5
                if dist_to_depot > 100:  # En az 100m uzaklıkta olsun
                    break

            # Rastgele paket ağırlığı (0.5 kg - 10 kg)
            weight = round(np.random.uniform(0.5, 10.0), 2)

            # Teslimat önceliği (1-5)
            priority = np.random.randint(1, 6)

            # Rastgele zaman aralığı (09:00 - 17:00 arası)
            start_time_hour = np.random.randint(start_hour, 16)
            start_time_min = np.random.choice([0, 15, 30, 45])
            end_time_hour = start_time_hour + np.random.randint(1, 3)
            end_time_min = np.random.choice([0, 15, 30, 45])

            # Bitiş zamanı 17:00'ı geçmesin
            if end_time_hour > 17:
                end_time_hour = 17
                end_time_min = 0

            time_window = (
                f"{start_time_hour:02d}:{start_time_min:02d}",
                f"{end_time_hour:02d}:{end_time_min:02d}"
            )

            delivery_point = {
                "id": i,
                "pos": (round(pos_x, 2), round(pos_y, 2)),
                "weight": weight,
                "priority": priority,
                "time_window": time_window
            }

            self.delivery_points.append(delivery_point)

        return self.delivery_points

    def generate_no_fly_zones(self):
        """Uçuşa yasak bölgeleri oluştur"""
        self.no_fly_zones = []

        min_vertices = 3  # En az üçgen
        max_vertices = 6  # En fazla altıgen

        for i in range(self.num_no_fly_zones):
            # Poligonun merkezi
            center_x = np.random.uniform(100, self.area_size[0] - 100)
            center_y = np.random.uniform(100, self.area_size[1] - 100)

            # Merkez nokta depodan ve teslimat noktalarından uzak olsun
            too_close = True
            max_attempts = 50
            attempts = 0

            while too_close and attempts < max_attempts:
                too_close = False

                # Depodan uzaklık kontrolü
                dist_to_depot = ((center_x - self.depot_position[0]) ** 2 +
                                 (center_y - self.depot_position[1]) ** 2) ** 0.5
                if dist_to_depot < 200:  # En az 200m uzaklıkta olsun
                    too_close = True

                # Teslimat noktalarından uzaklık kontrolü
                for dp in self.delivery_points:
                    dist_to_dp = ((center_x - dp["pos"][0]) ** 2 +
                                  (center_y - dp["pos"][1]) ** 2) ** 0.5
                    if dist_to_dp < 150:  # En az 150m uzaklıkta olsun
                        too_close = True
                        break

                if too_close:
                    center_x = np.random.uniform(100, self.area_size[0] - 100)
                    center_y = np.random.uniform(100, self.area_size[1] - 100)
                    attempts += 1

            # Polygun büyüklüğü
            radius = np.random.uniform(50, 150)

            # Köşe sayısı
            num_vertices = np.random.randint(min_vertices, max_vertices + 1)

            # Poligon köşelerini oluştur
            coordinates = []
            for j in range(num_vertices):
                angle = 2 * np.pi * j / num_vertices
                # Düzensiz poligon için rastgele varyasyon
                r = radius * np.random.uniform(0.8, 1.2)
                x = center_x + r * np.cos(angle)
                y = center_y + r * np.sin(angle)
                coordinates.append((round(x, 2), round(y, 2)))

            # Rastgele zaman aralığı (aktif olduğu saatler)
            start_time_hour = np.random.randint(9, 16)
            start_time_min = np.random.choice([0, 15, 30, 45])
            duration_hours = np.random.randint(1, 4)

            end_time_hour = start_time_hour + duration_hours
            end_time_min = start_time_min

            # Bitiş zamanı 17:00'ı geçmesin
            if end_time_hour > 17:
                end_time_hour = 17
                end_time_min = 0

            active_time = (
                f"{start_time_hour:02d}:{start_time_min:02d}",
                f"{end_time_hour:02d}:{end_time_min:02d}"
            )

            no_fly_zone = {
                "id": i,
                "coordinates": coordinates,
                "active_time": active_time
            }

            self.no_fly_zones.append(no_fly_zone)

        return self.no_fly_zones

    def generate_all_data(self):
        """Tüm veri setini oluştur"""
        self.generate_drones()
        self.generate_delivery_points()
        self.generate_no_fly_zones()

        return {
            "drones": self.drones,
            "delivery_points": self.delivery_points,
            "no_fly_zones": self.no_fly_zones,
            "depot": self.depot_position
        }

    def save_to_file(self, filename="drone_data.json"):
        """Veriyi JSON formatında dosyaya kaydet"""
        data = self.generate_all_data()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"Veri başarıyla {filename} dosyasına kaydedildi.")

        # Ayrıca okunması kolay metin formatında da kaydet
        txt_filename = filename.replace('.json', '.txt')
        self.save_as_text(txt_filename)

        return filename

    def save_as_text(self, filename="drone_data.txt"):
        """Veriyi okunması kolay metin formatında kaydet"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("DRONE FİLO OPTİMİZASYONU VERİ SETİ\n")
            f.write("=" * 40 + "\n\n")

            f.write(f"Depo Konumu: {self.depot_position}\n\n")

            f.write("DRONE BİLGİLERİ\n")
            f.write("-" * 40 + "\n")
            f.write(
                f"{'ID':<5}{'Max Ağırlık (kg)':<20}{'Batarya (mAh)':<20}{'Hız (m/s)':<15}{'Başlangıç Konumu':<20}\n")

            for drone in self.drones:
                # Tuple'ı string olarak biçimlendir
                start_pos_str = f"({drone['start_pos'][0]}, {drone['start_pos'][1]})"
                f.write(
                    f"{drone['id']:<5}{drone['max_weight']:<20}{drone['battery']:<20}{drone['speed']:<15}{start_pos_str}\n")

            f.write("\n\nTESLİMAT NOKTALARI\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'ID':<5}{'Konum':<25}{'Ağırlık (kg)':<15}{'Öncelik':<10}{'Zaman Aralığı':<20}\n")

            for dp in self.delivery_points:
                # Tuple'ı string olarak biçimlendir
                pos_str = f"({dp['pos'][0]}, {dp['pos'][1]})"
                time_window_str = f"{dp['time_window'][0]}-{dp['time_window'][1]}"
                f.write(f"{dp['id']:<5}{pos_str:<25}{dp['weight']:<15}{dp['priority']:<10}{time_window_str}\n")

            f.write("\n\nUÇUŞA YASAK BÖLGELER\n")
            f.write("-" * 80 + "\n")

            for nfz in self.no_fly_zones:
                f.write(f"ID: {nfz['id']}\n")
                # Tuple'ı string olarak biçimlendir
                time_str = f"{nfz['active_time'][0]}-{nfz['active_time'][1]}"
                f.write(f"Aktif Zaman: {time_str}\n")
                f.write("Koordinatlar:\n")
                for coord in nfz['coordinates']:
                    coord_str = f"({coord[0]}, {coord[1]})"
                    f.write(f"  {coord_str}\n")
                f.write("\n")

        print(f"Veri başarıyla {filename} dosyasına metin formatında kaydedildi.")

    def visualize(self, save_fig=False, filename="drone_scenario.png"):
        """Oluşturulan senaryoyu görselleştir"""
        plt.figure(figsize=(10, 10))

        # Alanı çiz
        plt.xlim(0, self.area_size[0])
        plt.ylim(0, self.area_size[1])

        # Depoyu çiz
        plt.plot(self.depot_position[0], self.depot_position[1], 'bD', markersize=10, label='Depo')

        # Teslimat noktalarını çiz
        for dp in self.delivery_points:
            plt.plot(dp["pos"][0], dp["pos"][1], 'ro', markersize=6)
            plt.text(dp["pos"][0] + 10, dp["pos"][1] + 10, f"DP{dp['id']}\nP{dp['priority']}", fontsize=8)

        # No-fly zone'ları çiz
        for nfz in self.no_fly_zones:
            coords = nfz["coordinates"]
            polygon = patches.Polygon(coords, closed=True, fill=True, alpha=0.3, color='red')
            plt.gca().add_patch(polygon)

            # No-fly zone'un ortalamasını bul
            center_x = sum([c[0] for c in coords]) / len(coords)
            center_y = sum([c[1] for c in coords]) / len(coords)
            plt.text(center_x, center_y, f"NFZ{nfz['id']}\n{nfz['active_time'][0]}-{nfz['active_time'][1]}",
                     fontsize=8, ha='center')

        plt.title("Drone Filo Optimizasyon Senaryosu")
        plt.xlabel("X (metre)")
        plt.ylabel("Y (metre)")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()

        if save_fig:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Görsel {filename} dosyasına kaydedildi.")

        plt.show()