CREATE TABLE `Addresses` (
`address_id` INTEGER PRIMARY KEY,
`address_details` VARCHAR(255)
);

CREATE TABLE `Customer_Orders` (
`order_id` INTEGER PRIMARY KEY,
`customer_id` INTEGER NOT NULL,
`order_date` DATETIME NOT NULL,
`order_status_code` VARCHAR(15),
FOREIGN KEY (`customer_id` ) REFERENCES `Customers`(`customer_id` )
);

CREATE TABLE `Customers` (
`customer_id` INTEGER PRIMARY KEY,
`address_id` INTEGER NOT NULL,
`payment_method_code` VARCHAR(15),
`customer_number` VARCHAR(20),
`customer_name` VARCHAR(80),
`customer_address` VARCHAR(255),
`customer_phone` VARCHAR(80),
`customer_email` VARCHAR(80)
);

CREATE TABLE `Order_Items` (
`order_item_id` INTEGER NOT NULL ,
`order_id` INTEGER NOT NULL,
`product_id` INTEGER NOT NULL,
`order_quantity` VARCHAR(80),
FOREIGN KEY (`order_id` ) REFERENCES `Customer_Orders`(`order_id` ),
FOREIGN KEY (`product_id` ) REFERENCES `Products`(`product_id` )
);

CREATE TABLE `Products` (
`product_id` INTEGER PRIMARY KEY,
`product_type_code` VARCHAR(15),
`product_name` VARCHAR(80),
`product_price` DOUBLE NULL
);

