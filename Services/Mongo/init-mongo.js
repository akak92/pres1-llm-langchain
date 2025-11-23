// Script de inicialización de MongoDB
// Este script se ejecuta automáticamente cuando se inicia el contenedor de MongoDB

// Conectar a la base de datos 'store'
db = db.getSiblingDB('store');

// Crear la colección 'products' e insertar 20 documentos de ejemplo
db.products.insertMany([
  {
    name: "Laptop HP Pavilion",
    unit_price: 899.99,
    stock: 15
  },
  {
    name: "Mouse Logitech MX Master",
    unit_price: 79.99,
    stock: 25
  },
  {
    name: "Teclado Mecánico RGB",
    unit_price: 129.50,
    stock: 12
  },
  {
    name: "Monitor 27 pulgadas 4K",
    unit_price: 299.99,
    stock: 8
  },
  {
    name: "Auriculares Sony WH-1000XM4",
    unit_price: 349.99,
    stock: 18
  },
  {
    name: "SSD Samsung 1TB",
    unit_price: 159.99,
    stock: 30
  },
  {
    name: "Webcam Logitech C920",
    unit_price: 89.99,
    stock: 22
  },
  {
    name: "Smartphone Samsung Galaxy S23",
    unit_price: 799.99,
    stock: 10
  },
  {
    name: "Tablet iPad Air",
    unit_price: 599.99,
    stock: 14
  },
  {
    name: "Impresora Canon PIXMA",
    unit_price: 199.99,
    stock: 7
  },
  {
    name: "Router WiFi 6 ASUS",
    unit_price: 179.99,
    stock: 16
  },
  {
    name: "Cable HDMI 4K",
    unit_price: 19.99,
    stock: 50
  },
  {
    name: "Disco Duro Externo 2TB",
    unit_price: 89.99,
    stock: 20
  },
  {
    name: "Cargador Inalámbrico",
    unit_price: 39.99,
    stock: 35
  },
  {
    name: "Adaptador USB-C Hub",
    unit_price: 49.99,
    stock: 28
  },
  {
    name: "Altavoces Bluetooth JBL",
    unit_price: 119.99,
    stock: 13
  },
  {
    name: "Cámara GoPro Hero 11",
    unit_price: 499.99,
    stock: 9
  },
  {
    name: "Powerbank 20000mAh",
    unit_price: 59.99,
    stock: 24
  },
  {
    name: "Smartwatch Apple Watch SE",
    unit_price: 279.99,
    stock: 11
  },
  {
    name: "Micrófono Blue Yeti",
    unit_price: 149.99,
    stock: 6
  }
]);

// Verificar que los documentos se insertaron correctamente
print("Base de datos 'store' creada exitosamente");
print("Colección 'products' creada con " + db.products.countDocuments() + " documentos");

// Crear un índice en el campo 'name' para optimizar búsquedas
db.products.createIndex({ "name": 1 });

print("Inicialización de MongoDB completada");