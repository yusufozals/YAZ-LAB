class Drone:
    def __init__(self, id, max_weight, battery, speed, start_pos):
        """
        Drone sınıfı

        Parametreler:
        -------------
        id : int
            Drone'un benzersiz ID'si
        max_weight : float
            Drone'un taşıyabileceği maksimum ağırlık (kg)
        battery : int
            Drone'un batarya kapasitesi (mAh)
        speed : float
            Drone'un hızı (m/s)
        start_pos : tuple
            Drone'un başlangıç koordinatları (x, y)
        """
        self.id = id
        self.max_weight = max_weight
        self.battery = battery
        self.speed = speed
        self.start_pos = start_pos

        # Ek özellikler
        self.current_pos = start_pos
        self.current_battery = battery  # Mevcut batarya durumu
        self.current_load = 0.0  # Mevcut taşınan yük
        self.route = [start_pos]  # Drone'un izlediği rota
        self.delivered_packages = []  # Teslim edilen paketler

    def can_carry(self, weight):
        """Drone'un belirli bir ağırlığı taşıyıp taşıyamayacağını kontrol eder"""
        return self.current_load + weight <= self.max_weight

    def add_package(self, package_weight):
        """Drone'a paket ekler ve mevcut yükü günceller"""
        if not self.can_carry(package_weight):
            return False
        self.current_load += package_weight
        return True

    def remove_package(self, package_weight):
        """Drone'dan paket çıkarır ve mevcut yükü günceller"""
        self.current_load = max(0, self.current_load - package_weight)
        return True

    def move_to(self, new_pos):
        """Drone'u yeni bir konuma hareket ettirir"""
        # Eski ve yeni konum arasındaki mesafeyi hesapla
        distance = ((new_pos[0] - self.current_pos[0]) ** 2 +
                    (new_pos[1] - self.current_pos[1]) ** 2) ** 0.5

        # Hareket için gereken süre (saniye)
        time_required = distance / self.speed

        # Batarya tüketimi (basit model: her 100m için 10mAh tüket)
        battery_consumption = distance / 100 * 10

        # Batarya kontrolü
        if battery_consumption > self.current_battery:
            return False  # Yetersiz batarya

        # Hareket gerçekleştir
        self.current_pos = new_pos
        self.current_battery -= battery_consumption
        self.route.append(new_pos)

        return time_required

    def deliver_package(self, package_id, package_weight):
        """Paketi teslim eder"""
        self.delivered_packages.append(package_id)
        self.remove_package(package_weight)
        return True

    def return_to_base(self, depot_pos):
        """Drone'u depoya geri döndürür"""
        return self.move_to(depot_pos)

    def recharge(self, time_hours=1):
        """Drone'u şarj eder (1 saatte tam şarj varsayılıyor)"""
        charge_rate = self.battery / 1.0  # 1 saatte tam şarj
        charge_amount = charge_rate * time_hours
        self.current_battery = min(self.battery, self.current_battery + charge_amount)
        return time_hours

    def get_status(self):
        """Drone'un mevcut durumunu alır"""
        return {
            "id": self.id,
            "current_pos": self.current_pos,
            "current_battery": self.current_battery,
            "current_battery_percentage": (self.current_battery / self.battery) * 100,
            "current_load": self.current_load,
            "max_weight": self.max_weight,
            "load_percentage": (self.current_load / self.max_weight) * 100 if self.max_weight > 0 else 0,
            "deliveries_made": len(self.delivered_packages)
        }

    def to_dict(self):
        """Drone verilerini sözlük olarak döndürür"""
        return {
            "id": self.id,
            "max_weight": self.max_weight,
            "battery": self.battery,
            "speed": self.speed,
            "start_pos": self.start_pos,
            "current_battery": self.current_battery,
            "current_load": self.current_load,
            "route": self.route,
            "delivered_packages": self.delivered_packages
        }

    @classmethod
    def from_dict(cls, data):
        """Sözlükten Drone nesnesi oluşturur"""
        drone = cls(
            id=data["id"],
            max_weight=data["max_weight"],
            battery=data["battery"],
            speed=data["speed"],
            start_pos=data["start_pos"]
        )

        # Ek özellikleri yükle (mevcutsa)
        if "current_battery" in data:
            drone.current_battery = data["current_battery"]
        if "current_load" in data:
            drone.current_load = data["current_load"]
        if "route" in data:
            drone.route = data["route"]
        if "delivered_packages" in data:
            drone.delivered_packages = data["delivered_packages"]

        return drone