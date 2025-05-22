from datetime import datetime


class NoFlyZone:
    def __init__(self, id, coordinates, active_time):
        """
        Uçuşa Yasak Bölge sınıfı

        Parametreler:
        -------------
        id : int
            Uçuşa yasak bölgenin benzersiz ID'si
        coordinates : list
            Bölgenin köşe noktaları, [(x1,y1), (x2,y2), ...]
        active_time : tuple
            Bölgenin aktif olduğu zaman aralığı ("09:30", "11:00")
        """
        self.id = id
        self.coordinates = coordinates
        self.active_time = active_time

    def is_active(self, current_time):
        """
        Bölgenin belirli bir zamanda aktif olup olmadığını kontrol eder

        Parametreler:
        -------------
        current_time : str
            Mevcut zaman ("HH:MM" formatında)

        Dönüş:
        ------
        bool
            Bölge aktifse True, değilse False
        """
        start_time, end_time = self.active_time
        return start_time <= current_time <= end_time

    def is_point_inside(self, point):
        """
        Bir noktanın no-fly zone içinde olup olmadığını kontrol eder (Ray Casting algoritması)

        Parametreler:
        -------------
        point : tuple
            Kontrol edilecek nokta (x, y)

        Dönüş:
        ------
        bool
            Nokta bölge içindeyse True, değilse False
        """
        x, y = point
        n = len(self.coordinates)
        inside = False

        p1x, p1y = self.coordinates[0]
        for i in range(n + 1):
            p2x, p2y = self.coordinates[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def does_line_intersect(self, start_point, end_point):
        """
        Bir çizginin (iki nokta arasındaki) no-fly zone ile kesişip kesişmediğini kontrol eder

        Parametreler:
        -------------
        start_point : tuple
            Çizginin başlangıç noktası (x, y)
        end_point : tuple
            Çizginin bitiş noktası (x, y)

        Dönüş:
        ------
        bool
            Çizgi bölge ile kesişiyorsa True, değilse False
        """
        # Çizginin kendisi bölge içinde mi kontrol et
        if self.is_point_inside(start_point) or self.is_point_inside(end_point):
            return True

        # Çizgi segmentinin bölgenin herhangi bir kenarıyla kesişip kesişmediğini kontrol et
        x1, y1 = start_point
        x2, y2 = end_point

        n = len(self.coordinates)
        for i in range(n):
            p1 = self.coordinates[i]
            p2 = self.coordinates[(i + 1) % n]

            x3, y3 = p1
            x4, y4 = p2

            # Çizgi segmentlerinin kesişip kesişmediğini kontrol et
            den = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            if den == 0:  # Çizgiler paralel
                continue

            ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
            ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den

            if 0 <= ua <= 1 and 0 <= ub <= 1:
                return True

        return False

    def to_dict(self):
        """Uçuşa yasak bölge verilerini sözlük olarak döndürür"""
        return {
            "id": self.id,
            "coordinates": self.coordinates,
            "active_time": self.active_time
        }

    @classmethod
    def from_dict(cls, data):
        """Sözlükten NoFlyZone nesnesi oluşturur"""
        return cls(
            id=data["id"],
            coordinates=data["coordinates"],
            active_time=data["active_time"]
        )