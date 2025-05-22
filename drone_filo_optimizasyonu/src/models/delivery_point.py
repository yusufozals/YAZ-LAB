class DeliveryPoint:
    def __init__(self, id, pos, weight, priority, time_window):
        """
        Teslimat Noktası sınıfı

        Parametreler:
        -------------
        id : int
            Teslimat noktasının benzersiz ID'si
        pos : tuple
            Teslimatın yapılacağı koordinatlar (x, y)
        weight : float
            Paketin ağırlığı (kg)
        priority : int
            Teslimatın öncelik seviyesi (1: düşük, 5: yüksek)
        time_window : tuple
            Teslimatın kabul edilebilir zaman aralığı ("09:00", "10:00")
        """
        self.id = id
        self.pos = pos
        self.weight = weight
        self.priority = priority
        self.time_window = time_window

        # Ek özellikler
        self.is_delivered = False
        self.delivered_time = None
        self.assigned_drone = None

    def assign_to_drone(self, drone_id):
        """Teslimat noktasını bir drone'a atar"""
        self.assigned_drone = drone_id
        return True

    def mark_as_delivered(self, time):
        """Teslimat noktasını teslim edildi olarak işaretler"""
        self.is_delivered = True
        self.delivered_time = time
        return True

    def is_in_time_window(self, time):
        """Verilen zamanın teslimat penceresi içinde olup olmadığını kontrol eder"""
        start_time, end_time = self.time_window
        return start_time <= time <= end_time

    def time_window_seconds(self):
        """Teslimat zaman penceresini saniye cinsinden döndürür"""
        start_time, end_time = self.time_window

        # HH:MM formatını parçala
        start_hour, start_min = map(int, start_time.split(':'))
        end_hour, end_min = map(int, end_time.split(':'))

        # Saniyeye çevir
        start_seconds = start_hour * 3600 + start_min * 60
        end_seconds = end_hour * 3600 + end_min * 60

        return (start_seconds, end_seconds)

    def to_dict(self):
        """Teslimat noktası verilerini sözlük olarak döndürür"""
        return {
            "id": self.id,
            "pos": self.pos,
            "weight": self.weight,
            "priority": self.priority,
            "time_window": self.time_window,
            "is_delivered": self.is_delivered,
            "delivered_time": self.delivered_time,
            "assigned_drone": self.assigned_drone
        }

    @classmethod
    def from_dict(cls, data):
        """Sözlükten DeliveryPoint nesnesi oluşturur"""
        delivery_point = cls(
            id=data["id"],
            pos=data["pos"],
            weight=data["weight"],
            priority=data["priority"],
            time_window=data["time_window"]
        )

        # Ek özellikleri yükle (mevcutsa)
        if "is_delivered" in data:
            delivery_point.is_delivered = data["is_delivered"]
        if "delivered_time" in data:
            delivery_point.delivered_time = data["delivered_time"]
        if "assigned_drone" in data:
            delivery_point.assigned_drone = data["assigned_drone"]

        return delivery_point