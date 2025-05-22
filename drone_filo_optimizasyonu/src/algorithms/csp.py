import numpy as np
from constraint import Problem, AllDifferentConstraint


class DroneCSP:
    def __init__(self, drones, delivery_points, no_fly_zones, depot_position):
        """
        Drone atama problemi için Kısıt Tatmin Problemi (CSP) çözücü

        Parametreler:
        -------------
        drones : list
            Drone nesnelerinin listesi
        delivery_points : list
            DeliveryPoint nesnelerinin listesi
        no_fly_zones : list
            NoFlyZone nesnelerinin listesi
        depot_position : tuple
            Depo konumu (x, y)
        """
        self.drones = drones
        self.delivery_points = delivery_points
        self.no_fly_zones = no_fly_zones
        self.depot_position = depot_position
        self.problem = Problem()

    def add_variables(self):
        """CSP problemi için değişkenleri ekler"""
        # Değişkenler: Her teslimat noktası hangi drone'a atanacak
        for i, dp in enumerate(self.delivery_points):
            # Her teslimat noktası bir drone'a atanabilir
            self.problem.addVariable(f"delivery_{dp.id}", list(range(len(self.drones))))

    def add_capacity_constraints(self):
        """Kapasite kısıtlarını ekler"""

        # Her drone'un taşıma kapasitesi sınırını kontrol et

        def capacity_constraint(*assignments):
            """Her drone için toplam yük taşıma kapasitesini kontrol eder"""
            # Drone başına toplam yükü hesapla
            drone_loads = [0] * len(self.drones)

            for i, drone_id in enumerate(assignments):
                dp = self.delivery_points[i]
                drone_loads[drone_id] += dp.weight

            # Her drone için kapasite kontrolü
            for i, load in enumerate(drone_loads):
                if load > self.drones[i].max_weight:
                    return False

            return True

        delivery_vars = [f"delivery_{dp.id}" for dp in self.delivery_points]
        self.problem.addConstraint(capacity_constraint, delivery_vars)

    def add_time_window_constraints(self):
        """Zaman penceresi kısıtlarını ekler"""

        def time_window_constraint(*assignments):
            """Teslimatların zamanında yapılıp yapılamayacağını kontrol eder"""
            # Her drone için rotaları ve zamanlamaları hesapla
            drone_routes = [[] for _ in range(len(self.drones))]
            drone_times = [0] * len(self.drones)  # Başlangıç zamanı (saniye)

            # 09:00'dan başla (saniye cinsinden)
            start_time_seconds = 9 * 3600

            # Her drone depodan başlar
            for i in range(len(self.drones)):
                drone_routes[i].append(self.depot_position)
                drone_times[i] = start_time_seconds

            # Teslimatları drone'lara ata
            for i, drone_id in enumerate(assignments):
                dp = self.delivery_points[i]

                # Drone'un mevcut konumu
                current_pos = drone_routes[drone_id][-1]

                # Drone'un teslimat noktasına gitmesi
                distance = np.sqrt((current_pos[0] - dp.pos[0]) ** 2 + (current_pos[1] - dp.pos[1]) ** 2)
                travel_time = distance / self.drones[drone_id].speed  # Saniye cinsinden seyahat süresi

                # Yeni konum ve zaman
                drone_routes[drone_id].append(dp.pos)
                drone_times[drone_id] += travel_time

                # Teslimat penceresini kontrol et
                start_window, end_window = dp.time_window_seconds()
                if drone_times[drone_id] < start_window:
                    # Drone erken geldi, bekleme zamanı
                    drone_times[drone_id] = start_window
                elif drone_times[drone_id] > end_window:
                    # Drone geç kaldı, kısıt ihlali
                    return False

                # Teslimat işlemi için süre ekle (1 dakika)
                drone_times[drone_id] += 60

            return True

        delivery_vars = [f"delivery_{dp.id}" for dp in self.delivery_points]
        self.problem.addConstraint(time_window_constraint, delivery_vars)

    def add_no_fly_zone_constraints(self):
        """No-fly zone kısıtlarını ekler"""

        def no_fly_zone_constraint(*assignments):
            """Rotanın no-fly zone'lardan geçip geçmediğini kontrol eder"""
            # Her drone için rotaları hesapla
            drone_routes = [[] for _ in range(len(self.drones))]

            # Her drone depodan başlar
            for i in range(len(self.drones)):
                drone_routes[i].append(self.depot_position)

            # Teslimatları drone'lara ata
            for i, drone_id in enumerate(assignments):
                dp = self.delivery_points[i]
                drone_routes[drone_id].append(dp.pos)

            # Her bir drone rotasını kontrol et
            for drone_id, route in enumerate(drone_routes):
                for i in range(len(route) - 1):
                    start_pos = route[i]
                    end_pos = route[i + 1]

                    # Bu yol segmenti herhangi bir no-fly zone ile kesişiyor mu?
                    for nfz in self.no_fly_zones:
                        if nfz.does_line_intersect(start_pos, end_pos):
                            return False

            return True

        delivery_vars = [f"delivery_{dp.id}" for dp in self.delivery_points]
        self.problem.addConstraint(no_fly_zone_constraint, delivery_vars)

    def add_battery_constraints(self):
        """Batarya kısıtlarını ekler"""

        def battery_constraint(*assignments):
            """Drone'ların batarya kapasitesini kontrol eder"""
            # Her drone için batarya tüketimini hesapla
            drone_distances = [0] * len(self.drones)

            # Her drone için rotaları hesapla
            drone_routes = [[] for _ in range(len(self.drones))]

            # Her drone depodan başlar
            for i in range(len(self.drones)):
                drone_routes[i].append(self.depot_position)

            # Teslimatları drone'lara ata
            for i, drone_id in enumerate(assignments):
                dp = self.delivery_points[i]
                drone_routes[drone_id].append(dp.pos)

            # Her drone'u depoya geri döndür
            for i in range(len(self.drones)):
                drone_routes[i].append(self.depot_position)

            # Her bir drone rotası için toplam mesafeyi hesapla
            for drone_id, route in enumerate(drone_routes):
                for i in range(len(route) - 1):
                    start_pos = route[i]
                    end_pos = route[i + 1]

                    # Mesafeyi hesapla
                    distance = np.sqrt((start_pos[0] - end_pos[0]) ** 2 + (start_pos[1] - end_pos[1]) ** 2)
                    drone_distances[drone_id] += distance

            # Her drone için batarya kapasitesini kontrol et
            for drone_id, distance in enumerate(drone_distances):
                # Basit batarya modeli: her 100m için 10mAh tüketim
                battery_consumption = distance / 100 * 10

                if battery_consumption > self.drones[drone_id].battery:
                    return False

            return True

        delivery_vars = [f"delivery_{dp.id}" for dp in self.delivery_points]
        self.problem.addConstraint(battery_constraint, delivery_vars)

    def add_balanced_load_constraints(self):
        """Dengeli yük dağılımı kısıtlarını ekler (isteğe bağlı)"""

        def balanced_load_constraint(*assignments):
            """Drone'lar arasında dengeli yük dağılımı olmasını sağlar"""
            # Her drone'a kaç teslimat atandığını say
            drone_counts = [0] * len(self.drones)

            for drone_id in assignments:
                drone_counts[drone_id] += 1

            # En çok ve en az teslimat sayıları arasındaki fark
            max_deliveries = max(drone_counts)
            min_deliveries = min(drone_counts)

            # Fark en fazla 2 olmalı
            return max_deliveries - min_deliveries <= 2

        delivery_vars = [f"delivery_{dp.id}" for dp in self.delivery_points]
        self.problem.addConstraint(balanced_load_constraint, delivery_vars)

    def solve(self):
        """CSP problemini çözer ve atama sonuçlarını döndürür"""
        self.add_variables()
        self.add_capacity_constraints()
        self.add_time_window_constraints()
        self.add_no_fly_zone_constraints()
        self.add_battery_constraints()
        self.add_balanced_load_constraints()

        # Problemi çöz
        solutions = self.problem.getSolutions()

        if not solutions:
            print("CSP çözümü bulunamadı!")
            return None

        # İlk çözümü al (veya en iyi çözümü bulmak için bir değerlendirme fonksiyonu eklenebilir)
        solution = solutions[0]

        # Sonucu düzenle: {drone_id: [delivery_ids]}
        assignments = {i: [] for i in range(len(self.drones))}

        for var, drone_id in solution.items():
            if var.startswith("delivery_"):
                delivery_id = int(var.split("_")[1])
                assignments[drone_id].append(delivery_id)

        return assignments