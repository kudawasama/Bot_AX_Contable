from license_manager import generate_key, get_hwid
import sys

def main():
    print("\n" + "="*50)
    print("  Bot AX Contable - Generador de Licencias      ")
    print("="*50 + "\n")
    
    print(f"Tu HWID Actual: {get_hwid()}\n")
    
    while True:
        try:
            target_id = input("Ingresa el ID de Hardware (HWID) del cliente (o 'salir'): ").strip().upper()
            if target_id.lower() == 'salir': break
            
            if not target_id: continue
            
            key = generate_key(target_id)
            print("-" * 30)
            print(f"LLAVE PARA {target_id}:")
            print(f">>> {key} <<<")
            print("-" * 30)
            
            save = input("¿Guardar en archivo 'license.key'? (s/n): ").lower()
            if save == 's':
                with open("license.key", "w") as f:
                    f.write(key)
                print("¡Archivo license.key guardado correctamente!")
            
            print("\n")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
