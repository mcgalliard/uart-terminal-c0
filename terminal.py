import serial
import time

# Change this to match your USB serial port
SERIAL_PORT = 'COM9'
BAUD_RATE = 115200

def open_serial(port, baudrate):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Connected to {port} at {baudrate} baud.")
        return ser
    except serial.SerialException as e:
        print(f"Failed to open serial port: {e}")
        return None

def read_register(ser, address):
    cmd = f"read 0x{address:X}\r\n"
    ser.write(cmd.encode())
    response = ser.readline().decode().strip()
    return response

def write_register(ser, address, value):
    cmd = f"write 0x{address:X} 0x{value:X}\r\n"
    ser.write(cmd.encode())
    response = ser.readline().decode().strip()
    return response

def main():
    ser = open_serial(SERIAL_PORT, BAUD_RATE)
    if ser is None:
        return

    while True:
        try:
            user_input = input(">> ").strip()
            if user_input == "exit":
                print("Exiting...")
                break
            elif user_input.startswith("read "):
                _, addr_str = user_input.split()
                addr = int(addr_str, 16)
                resp = read_register(ser, addr)
                print(f"{resp}")
            elif user_input.startswith("write "):
                _, addr_str, val_str = user_input.split()
                addr = int(addr_str, 16)
                val = int(val_str, 16)
                resp = write_register(ser, addr, val)
                print(f"{resp}")
            else:
                print("Invalid command. Use: read 0xADDR or write 0xADDR 0xVALUE")
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

    ser.close()

if __name__ == "__main__":
    main()
