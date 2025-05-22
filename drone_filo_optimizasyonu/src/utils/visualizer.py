import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import numpy as np
from matplotlib.animation import FuncAnimation
import networkx as nx


class DroneVisualizer:
    def __init__(self, drones, delivery_points, no_fly_zones, depot_position, area_size=(1000, 1000)):
        """
        Drone senaryosu için görselleştirici

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
        area_size : tuple
            Çalışma alanının boyutları (x, y)
        """
        self.drones = drones
        self.delivery_points = delivery_points
        self.no_fly_zones = no_fly_zones
        self.depot_position = depot_position
        self.area_size = area_size

        # Renk haritası oluştur
        self.drone_colors = cm.rainbow(np.linspace(0, 1, len(drones)))

    def plot_scenario(self, routes=None, show=True, save_path=None):
        """
        Senaryo haritasını çizer

        Parametreler:
        -------------
        routes : dict, optional
            Drone rotaları {drone_id: [(x1,y1), (x2,y2), ...]}
        show : bool
            True ise sonucu göster
        save_path : str, optional
            Eğer verilmişse, görüntüyü kaydet
        """
        plt.figure(figsize=(12, 10))

        # Alanı çiz
        plt.xlim(0, self.area_size[0])
        plt.ylim(0, self.area_size[1])

        # Depo konumu
        plt.plot(self.depot_position[0], self.depot_position[1], 'ks', markersize=12, label='Depo')

        # No-fly zones
        for i, nfz in enumerate(self.no_fly_zones):
            poly = patches.Polygon(nfz.coordinates, closed=True, alpha=0.3,
                                   facecolor='red', edgecolor='darkred', label='No-Fly Zone' if i == 0 else "")
            plt.gca().add_patch(poly)

            # Zone merkezi
            center_x = sum(x for x, _ in nfz.coordinates) / len(nfz.coordinates)
            center_y = sum(y for _, y in nfz.coordinates) / len(nfz.coordinates)
            plt.text(center_x, center_y, f"NFZ{nfz.id}\n{nfz.active_time[0]}-{nfz.active_time[1]}",
                     fontsize=10, ha='center', color='darkred')

        # Teslimat noktaları
        for dp in self.delivery_points:
            plt.plot(dp.pos[0], dp.pos[1], 'bo', markersize=8)
            plt.text(dp.pos[0] + 5, dp.pos[1] + 5, f"DP{dp.id}\nP{dp.priority}\n{dp.weight}kg",
                     fontsize=8)

        # Rotaları çiz (eğer verilmişse)
        if routes:
            for drone_id, route in routes.items():
                color = self.drone_colors[drone_id]

                # Rotayı çiz
                xs = [point[0] for point in route]
                ys = [point[1] for point in route]
                plt.plot(xs, ys, '-', color=color, linewidth=2,
                         label=f"Drone {drone_id} (Max: {self.drones[drone_id].max_weight}kg)")

                # Ok işaretleri ekle
                for i in range(len(route) - 1):
                    plt.arrow(xs[i], ys[i], (xs[i + 1] - xs[i]) * 0.8, (ys[i + 1] - ys[i]) * 0.8,
                              head_width=10, head_length=15, fc=color, ec=color, alpha=0.7)

        plt.grid(True, linestyle='--', alpha=0.7)
        plt.title('Drone Filo Optimizasyonu Senaryosu')
        plt.xlabel('X (metre)')
        plt.ylabel('Y (metre)')
        plt.legend(loc='upper right')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        if show:
            plt.show()
        else:
            plt.close()

    def plot_graph(self, graph, show=True, save_path=None):
        """
        Teslimat grafiğini çizer

        Parametreler:
        -------------
        graph : networkx.DiGraph
            Teslimat grafiği
        show : bool
            True ise sonucu göster
        save_path : str, optional
            Eğer verilmişse, görüntüyü kaydet
        """
        plt.figure(figsize=(12, 10))

        # Düğüm konumlarını al
        pos = nx.get_node_attributes(graph, 'pos')

        # Alanı çiz
        plt.xlim(0, self.area_size[0])
        plt.ylim(0, self.area_size[1])

        # Depoya özel işaret
        depot_node = [n for n, attr in graph.nodes(data=True) if attr.get('is_depot', False)]
        if depot_node:
            nx.draw_networkx_nodes(graph, pos, nodelist=depot_node, node_color='black',
                                   node_shape='s', node_size=200, label='Depo')

        # Teslimat noktalarını çiz
        delivery_nodes = [n for n, attr in graph.nodes(data=True) if attr.get('is_delivery', False)]
        if delivery_nodes:
            nx.draw_networkx_nodes(graph, pos, nodelist=delivery_nodes, node_color='blue',
                                   node_shape='o', node_size=100, label='Teslimat Noktaları')

        # Kenarları çiz
        nx.draw_networkx_edges(graph, pos, width=1.0, alpha=0.5, arrows=True)

        # Düğüm etiketleri
        nx.draw_networkx_labels(graph, pos, font_size=8)

        # No-fly zones
        for nfz in self.no_fly_zones:
            poly = patches.Polygon(nfz.coordinates, closed=True, alpha=0.3,
                                   facecolor='red', edgecolor='darkred', label='No-Fly Zone')
            plt.gca().add_patch(poly)

        plt.grid(True, linestyle='--', alpha=0.7)
        plt.title('Teslimat Grafiği')
        plt.xlabel('X (metre)')
        plt.ylabel('Y (metre)')
        plt.legend(loc='upper right')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        if show:
            plt.show()
        else:
            plt.close()

    def animate_routes(self, routes, output_path='animation.mp4', fps=10):
        """
        Drone rotalarının animasyonunu oluşturur

        Parametreler:
        -------------
        routes : dict
            Drone rotaları {drone_id: [(x1,y1), (x2,y2), ...]}
        output_path : str
            Animasyon çıktı dosyası
        fps : int
            Saniyedeki kare sayısı
        """
        fig, ax = plt.subplots(figsize=(12, 10))

        # Alanı ayarla
        ax.set_xlim(0, self.area_size[0])
        ax.set_ylim(0, self.area_size[1])

        # Depo ve teslimat noktalarını çiz (sabit)
        ax.plot(self.depot_position[0], self.depot_position[1], 'ks', markersize=12)
        for dp in self.delivery_points:
            ax.plot(dp.pos[0], dp.pos[1], 'bo', markersize=8)

        # No-fly zones
        for nfz in self.no_fly_zones:
            poly = patches.Polygon(nfz.coordinates, closed=True, alpha=0.3,
                                   facecolor='red', edgecolor='darkred')
            ax.add_patch(poly)

        # Drone'lar için boş çizgiler ve noktalar
        drone_lines = {}
        drone_points = {}

        for drone_id in routes:
            color = self.drone_colors[drone_id]
            line, = ax.plot([], [], '-', color=color, linewidth=2, alpha=0.5)
            point, = ax.plot([], [], 'o', color=color, markersize=10, label=f"Drone {drone_id}")
            drone_lines[drone_id] = line
            drone_points[drone_id] = point

        # Zaman bilgisi
        time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12)

        # En uzun route uzunluğunu bul
        max_route_len = max(len(route) for route in routes.values())

        def init():
            """Animasyon başlangıç durumu"""
            for line in drone_lines.values():
                line.set_data([], [])
            for point in drone_points.values():
                point.set_data([], [])
            time_text.set_text('')
            return list(drone_lines.values()) + list(drone_points.values()) + [time_text]

        def animate(i):
            """Her karedeki animasyon"""
            for drone_id, route in routes.items():
                # Rota geçmişi
                if i < len(route):
                    xs = [p[0] for p in route[:i + 1]]
                    ys = [p[1] for p in route[:i + 1]]
                    drone_lines[drone_id].set_data(xs, ys)

                    # Drone'un mevcut konumu
                    drone_points[drone_id].set_data(route[i][0], route[i][1])
                else:
                    # Route bitmiş, drone depoda kalsın
                    drone_points[drone_id].set_data(route[-1][0], route[-1][1])

            # Zaman bilgisi (09:00'dan başla)
            seconds_elapsed = i * 60  # Her adım 1 dakika
            hours = (seconds_elapsed // 3600) + 9  # 09:00'dan başla
            minutes = (seconds_elapsed % 3600) // 60
            time_text.set_text(f'Zaman: {hours:02d}:{minutes:02d}')

            return list(drone_lines.values()) + list(drone_points.values()) + [time_text]

        # Animasyonu oluştur
        ani = FuncAnimation(fig, animate, frames=max_route_len + 10,
                            init_func=init, blit=True, interval=1000 / fps)

        # Başlık ve grid
        ax.set_title('Drone Rotaları Animasyonu')
        ax.set_xlabel('X (metre)')
        ax.set_ylabel('Y (metre)')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='upper right')

        # Animasyonu kaydet
        ani.save(output_path, writer='ffmpeg', fps=fps, dpi=200)
        plt.close()