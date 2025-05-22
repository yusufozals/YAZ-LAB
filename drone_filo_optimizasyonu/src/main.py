import argparse
import json
import time
import os
import numpy as np
import matplotlib.pyplot as plt

from src.models.drone import Drone
from src.models.delivery_point import DeliveryPoint
from src.models.no_fly_zone import NoFlyZone

from src.algorithms.graph import DeliveryGraph
from src.algorithms.astar import AStarPathfinder
from src.algorithms.csp import DroneCSP
from src.algorithms.genetic import GeneticAlgorithm

from src.cuda.distance_kernel import calculate_distances_gpu, calculate_distances_numba
from src.cuda.collision_kernel import check_paths_against_no_fly_zones
from src.cuda.fitness_kernel import calculate_fitness_gpu

from src.utils.visualizer import DroneVisualizer
from src.utils.data_generator import DroneDataGenerator

def load_data(data_file):
    """Veri dosyasını yükler"""
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Drone nesneleri oluştur
    drones = [Drone.from_dict(drone) for drone in data['drones']]

    # Teslimat noktası nesneleri oluştur
    delivery_points = [DeliveryPoint.from_dict(dp) for dp in data['delivery_points']]

    # No-fly zone nesneleri oluştur
    no_fly_zones = [NoFlyZone.from_dict(nfz) for nfz in data['no_fly_zones']]

    # Depo konumu
    depot_position = tuple(data['depot'])

    return drones, delivery_points, no_fly_zones, depot_position


def run_a_star(drones, delivery_points, no_fly_zones, depot_position):
    """A* algoritmasını çalıştırır"""
    start_time = time.time()

    # A* algoritması
    pathfinder = AStarPathfinder(delivery_points, no_fly_zones, depot_position)

    # Her drone için rota bul
    routes = {}
    total_cost = 0

    # Teslimatları dronelar arasında basitçe böl
    deliveries_per_drone = len(delivery_points) // len(drones)

    for i, drone in enumerate(drones):
        # Bu drone'un teslimat noktaları
        start_idx = i * deliveries_per_drone
        end_idx = (i + 1) * deliveries_per_drone if i < len(drones) - 1 else len(delivery_points)

        # Teslimat ID'leri
        delivery_ids = [dp.id + 1 for dp in delivery_points[start_idx:end_idx]]  # +1 çünkü depo 0

        if not delivery_ids:
            routes[i] = [depot_position]
            continue

        # Rota bul
        route_ids, cost = pathfinder.find_optimal_route(0, delivery_ids)

        # ID'leri koordinatlara dönüştür
        route = [pathfinder.point_id_map[id] for id in route_ids]

        # Sonuçları sakla
        routes[i] = route
        total_cost += cost

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"A* algoritması çalışma süresi: {elapsed_time:.4f} saniye")
    print(f"Toplam maliyet: {total_cost:.2f}")

    return routes, total_cost, elapsed_time


def run_csp(drones, delivery_points, no_fly_zones, depot_position):
    """CSP algoritmasını çalıştırır"""
    start_time = time.time()

    # CSP çözücü
    csp_solver = DroneCSP(drones, delivery_points, no_fly_zones, depot_position)

    # CSP çöz
    assignments = csp_solver.solve()

    if assignments is None:
        print("CSP çözümü bulunamadı!")
        return None, float('inf'), time.time() - start_time

    # Her drone için rota oluştur
    routes = {}
    total_cost = 0

    for drone_id, delivery_ids in assignments.items():
        if not delivery_ids:
            routes[drone_id] = [depot_position]
            continue

        # A* ile rota bul
        pathfinder = AStarPathfinder(delivery_points, no_fly_zones, depot_position)

        # ID'leri 1'den başladığı için +1 ekle
        route_ids, cost = pathfinder.find_optimal_route(0, [dp_id + 1 for dp_id in delivery_ids])

        # ID'leri koordinatlara dönüştür
        route = [pathfinder.point_id_map[id] for id in route_ids]

        # Sonuçları sakla
        routes[drone_id] = route
        total_cost += cost

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"CSP algoritması çalışma süresi: {elapsed_time:.4f} saniye")
    print(f"Toplam maliyet: {total_cost:.2f}")

    return routes, total_cost, elapsed_time

def run_genetic_algorithm(drones, delivery_points, no_fly_zones, depot_position):
    """Genetik algoritma çalıştırır"""
    start_time = time.time()

    # Genetik algoritma
    ga = GeneticAlgorithm(drones, delivery_points, no_fly_zones, depot_position,
                         population_size=100, generations=50)

    # GA çalıştır
    assignments, fitness = ga.run()

    # Her drone için rota oluştur
    routes = {}
    total_cost = 0

    for drone_id, delivery_ids in assignments.items():
        if not delivery_ids:
            routes[drone_id] = [depot_position]
            continue

        # A* ile rota bul
        pathfinder = AStarPathfinder(delivery_points, no_fly_zones, depot_position)

        # ID'leri 1'den başladığı için +1 ekle
        route_ids, cost = pathfinder.find_optimal_route(0, [dp_id + 1 for dp_id in delivery_ids])

        # ID'leri koordinatlara dönüştür
        route = [pathfinder.point_id_map[id] for id in route_ids]

        # Sonuçları sakla
        routes[drone_id] = route
        total_cost += cost

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Genetik algoritma çalışma süresi: {elapsed_time:.4f} saniye")
    print(f"En iyi fitness: {fitness:.2f}")
    print(f"Toplam maliyet: {total_cost:.2f}")

    return routes, fitness, elapsed_time

def compare_algorithms(drones, delivery_points, no_fly_zones, depot_position):
    """Algoritmaları karşılaştırır"""
    print("\n=== Algoritma Karşılaştırması ===")

    # A* algoritması
    print("\nA* Algoritması çalıştırılıyor...")
    a_star_routes, a_star_cost, a_star_time = run_a_star(drones, delivery_points, no_fly_zones, depot_position)

    # CSP algoritması
    print("\nCSP Algoritması çalıştırılıyor...")
    csp_routes, csp_cost, csp_time = run_csp(drones, delivery_points, no_fly_zones, depot_position)

    # Genetik algoritma
    print("\nGenetik Algoritma çalıştırılıyor...")
    ga_routes, ga_fitness, ga_time = run_genetic_algorithm(drones, delivery_points, no_fly_zones, depot_position)

    # Sonuçları karşılaştır
    print("\n--- Karşılaştırma Sonuçları ---")
    print(f"A* Algoritması: Süre = {a_star_time:.4f}s, Maliyet = {a_star_cost:.2f}")
    if csp_routes:
        print(f"CSP Algoritması: Süre = {csp_time:.4f}s, Maliyet = {csp_cost:.2f}")
    else:
        print("CSP Algoritması: Çözüm bulunamadı")
    print(f"Genetik Algoritma: Süre = {ga_time:.4f}s, Fitness = {ga_fitness:.2f}")

    # Görselleştirme
    visualizer = DroneVisualizer(drones, delivery_points, no_fly_zones, depot_position)

    # Rotaları görselleştir
    print("\nA* rotaları görselleştiriliyor...")
    visualizer.plot_scenario(a_star_routes, show=False, save_path="visualizations/a_star_routes.png")

    if csp_routes:
        print("CSP rotaları görselleştiriliyor...")
        visualizer.plot_scenario(csp_routes, show=False, save_path="visualizations/csp_routes.png")

    print("GA rotaları görselleştiriliyor...")
    visualizer.plot_scenario(ga_routes, show=False, save_path="visualizations/ga_routes.png")

    # Performans grafikleri
    print("\nPerformans grafikleri oluşturuluyor...")
    plt.figure(figsize=(10, 6))

    algorithms = ["A*", "CSP", "GA"]
    times = [a_star_time, csp_time if csp_routes else 0, ga_time]

    plt.bar(algorithms, times, color=['blue', 'green', 'red'])
    plt.title("Algoritmaların Çalışma Süreleri")
    plt.xlabel("Algoritma")
    plt.ylabel("Süre (saniye)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.savefig("visualizations/performance_comparison.png")
    plt.close()

    # En iyi rotaları animasyona dönüştür
    best_routes = ga_routes  # Genetik algoritma genellikle daha iyi sonuçlar verir

    print("\nEn iyi rotaların animasyonu oluşturuluyor...")
    visualizer.animate_routes(best_routes, output_path="visualizations/drone_animation.mp4")

    print("\nKarşılaştırma tamamlandı. Sonuçlar visualizations/ dizininde kaydedildi.")

def analyze_performance(data_file, output_file):
    """Performans analizi yapar"""
    print("\n=== Performans Analizi ===")

    # Veriyi yükle
    drones, delivery_points, no_fly_zones, depot_position = load_data(data_file)

    # Farklı boyutlardaki problemler için performans testi
    delivery_counts = [10, 20, 30, 40, 50]
    a_star_times = []
    csp_times = []
    ga_times = []

    for count in delivery_counts:
        print(f"\nTest: {count} teslimat noktası")

        # İlk 'count' kadar teslimat noktasını al
        subset_deliveries = delivery_points[:min(count, len(delivery_points))]

        # A* algoritması
        start_time = time.time()
        pathfinder = AStarPathfinder(subset_deliveries, no_fly_zones, depot_position)
        delivery_ids = [dp.id + 1 for dp in subset_deliveries]
        pathfinder.find_optimal_route(0, delivery_ids)
        a_star_time = time.time() - start_time
        a_star_times.append(a_star_time)
        print(f"A* süresi: {a_star_time:.4f}s")

        # CSP algoritması
        start_time = time.time()
        csp_solver = DroneCSP(drones, subset_deliveries, no_fly_zones, depot_position)
        csp_solver.solve()
        csp_time = time.time() - start_time
        csp_times.append(csp_time)
        print(f"CSP süresi: {csp_time:.4f}s")

        # Genetik algoritma
        start_time = time.time()
        ga = GeneticAlgorithm(drones, subset_deliveries, no_fly_zones, depot_position,
                             population_size=50, generations=20)  # Hızlandırmak için küçük değerler
        ga.run()
        ga_time = time.time() - start_time
        ga_times.append(ga_time)
        print(f"GA süresi: {ga_time:.4f}s")

    # Performans grafikleri
    plt.figure(figsize=(12, 8))

    plt.plot(delivery_counts, a_star_times, 'b-', marker='o', label="A*")
    plt.plot(delivery_counts, csp_times, 'g-', marker='s', label="CSP")
    plt.plot(delivery_counts, ga_times, 'r-', marker='^', label="GA")

    plt.title("Algoritmalar için Çalışma Süresi Karşılaştırması")
    plt.xlabel("Teslimat Noktası Sayısı")
    plt.ylabel("Çalışma Süresi (saniye)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    plt.savefig(output_file)
    plt.close()

    print(f"\nPerformans analizi tamamlandı. Sonuçlar {output_file} dosyasına kaydedildi.")

def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="Drone Filo Optimizasyonu")
    parser.add_argument('--data', type=str, default="data/drone_data.json",
                      help="Veri dosyası (JSON)")
    parser.add_argument('--generate', action='store_true',
                      help="Yeni veri üret")
    parser.add_argument('--algorithm', type=str, choices=['astar', 'csp', 'ga', 'all'],
                      default='all', help="Çalıştırılacak algoritma")
    parser.add_argument('--analyze', action='store_true',
                      help="Performans analizi yap")

    args = parser.parse_args()

    # Klasörleri oluştur
    os.makedirs("visualizations", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Veri üret
    if args.generate:
        print("Yeni veri üretiliyor...")
        generator = DroneDataGenerator()
        generator.save_to_file(args.data)

        # Test senaryolarını da oluştur
        print("\nSenaryo 1 (5 drone, 20 teslimat, 2 no-fly zone) oluşturuluyor...")
        gen1 = DroneDataGenerator(num_drones=5, num_delivery_points=20, num_no_fly_zones=2, seed=42)
        gen1.save_to_file("data/senaryo1.json")

        print("\nSenaryo 2 (10 drone, 50 teslimat, 5 no-fly zone) oluşturuluyor...")
        gen2 = DroneDataGenerator(num_drones=10, num_delivery_points=50, num_no_fly_zones=5, seed=43)
        gen2.save_to_file("data/senaryo2.json")

    # Veriyi yükle
    drones, delivery_points, no_fly_zones, depot_position = load_data(args.data)

    print(f"\nYüklenen veri: {len(drones)} drone, {len(delivery_points)} teslimat noktası, {len(no_fly_zones)} no-fly zone")

    # Algoritmaları çalıştır
    if args.algorithm == 'astar' or args.algorithm == 'all':
        print("\nA* algoritması çalıştırılıyor...")
        routes, cost, elapsed_time = run_a_star(drones, delivery_points, no_fly_zones, depot_position)

        # Görselleştir
        visualizer = DroneVisualizer(drones, delivery_points, no_fly_zones, depot_position)
        visualizer.plot_scenario(routes, save_path="visualizations/a_star_routes.png")

    if args.algorithm == 'csp' or args.algorithm == 'all':
        print("\nCSP algoritması çalıştırılıyor...")
        routes, cost, elapsed_time = run_csp(drones, delivery_points, no_fly_zones, depot_position)

        if routes:
            # Görselleştir
            visualizer = DroneVisualizer(drones, delivery_points, no_fly_zones, depot_position)
            visualizer.plot_scenario(routes, save_path="visualizations/csp_routes.png")

    if args.algorithm == 'ga' or args.algorithm == 'all':
        print("\nGenetik algoritma çalıştırılıyor...")
        routes, fitness, elapsed_time = run_genetic_algorithm(drones, delivery_points, no_fly_zones, depot_position)

        # Görselleştir
        visualizer = DroneVisualizer(drones, delivery_points, no_fly_zones, depot_position)
        visualizer.plot_scenario(routes, save_path="visualizations/ga_routes.png")

        # Animasyon
        visualizer.animate_routes(routes, output_path="visualizations/drone_animation.mp4")

    # Algoritmaların karşılaştırması
    if args.algorithm == 'all':
        compare_algorithms(drones, delivery_points, no_fly_zones, depot_position)

    # Performans analizi
    if args.analyze:
        analyze_performance(args.data, "visualizations/performance_analysis.png")

if __name__ == "__main__":
    main()