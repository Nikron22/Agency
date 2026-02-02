CREATE DATABASE kyrswork;

CREATE TABLE Clients (
    client_id SERIAL PRIMARY KEY,
    name_client VARCHAR(20) NOT NULL,
    client_type VARCHAR(50) NOT NULL,
    phone_number VARCHAR(12) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    CONSTRAINT CK_name_client_FORMAT CHECK (
        name_client ~ '^[А-Яа-яЁё\s]+$' AND name_client !~ '\d'
    ),
    CONSTRAINT CK_client_type_FORMAT CHECK (
        client_type IN ('Продавец', 'Покупатель', 'Арендодатель', 'Арендатор')
    ),
    CONSTRAINT CK_phone_number_FORMAT CHECK (
        phone_number ~ '^\+?\d{11}$'
    ),
    CONSTRAINT CK_email_FORMAT CHECK (
        email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    )
);

CREATE TABLE Agents (
    agent_id SERIAL PRIMARY KEY,
    name_agent VARCHAR(20) NOT NULL,
    surname_agent VARCHAR(50) NOT NULL,
    patronymic_agent VARCHAR(50) NOT NULL,
    work_experience smallint NOT NULL,
    phone_number_agent VARCHAR(12) NOT NULL UNIQUE,
    email_agent VARCHAR(100) NOT NULL UNIQUE,
    password_agent VARCHAR(255) NOT NULL,
    CONSTRAINT CK_work_experience_FORMAT CHECK (work_experience >= 0),
    CONSTRAINT CK_name_agent_FORMAT CHECK (
        name_agent ~ '^[А-Яа-яЁё\s]+$' AND name_agent !~ '\d'
    ),
    CONSTRAINT CK_surname_agent_FORMAT CHECK (
        surname_agent ~ '^[А-Яа-яЁё\s]+$' AND surname_agent !~ '\d'
    ),
    CONSTRAINT CK_patronymic_agent_FORMAT CHECK (
        patronymic_agent ~ '^[А-Яа-яЁё\s]+$' AND patronymic_agent !~ '\d'
    ),
    CONSTRAINT CK_phone_number_agent_FORMAT CHECK (
        phone_number_agent ~ '^\+?\d{11}$'
    ),
    CONSTRAINT CK_email_agent_FORMAT CHECK (
        email_agent ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    ),
    CONSTRAINT CK_password_agent_FORMAT CHECK (
        LENGTH(password_agent) BETWEEN 60 AND 255
    )
);

CREATE TABLE Requests (
    request_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    price_request NUMERIC(15,2) NOT NULL,
    region_request VARCHAR(50) NOT NULL,
    area_request NUMERIC(10,2) NOT NULL,
    rooms_count_request INTEGER NOT NULL,
    funds_request NUMERIC(15,2) NOT NULL,
    CONSTRAINT FK_client FOREIGN KEY (client_id) REFERENCES Clients(client_id),
    CONSTRAINT FK_agent FOREIGN KEY (agent_id) REFERENCES Agents(agent_id),
    CONSTRAINT CK_price_request_FORMAT CHECK (price_request > 0),
    CONSTRAINT CK_region_request_FORMAT CHECK (LENGTH(region_request) <= 50),
    CONSTRAINT CK_area_request_FORMAT CHECK (area_request > 0),
    CONSTRAINT CK_rooms_count_request_FORMAT CHECK (rooms_count_request > 0),
    CONSTRAINT CK_funds_request_FORMAT CHECK (funds_request > 0)
);

CREATE TABLE Properties (
    property_id SERIAL PRIMARY KEY,
    price_properties NUMERIC(15,2) NOT NULL,
    lift_properties VARCHAR(5) NOT NULL,
    territory_comfort_properties VARCHAR(255) NOT NULL,
    area_properties NUMERIC(10,2) NOT NULL,
    build_year_properties INTEGER NOT NULL,
    rooms_count_properties INTEGER NOT NULL,
    address_properties VARCHAR(100) NOT NULL,
    region_properties VARCHAR(50) NOT NULL,
    legal_aspects_properties VARCHAR(255) NOT NULL,
    floor_properties INTEGER NOT NULL,
    total_floors_properties INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    property_type VARCHAR(50) NOT NULL,
    is_available BOOLEAN DEFAULT true,
    CONSTRAINT fk_owner FOREIGN KEY (owner_id) REFERENCES Clients(client_id),
    CONSTRAINT CK_price_properties_FORMAT CHECK (price_properties > 0),
    CONSTRAINT CK_lift_properties_FORMAT CHECK (lift_properties IN ('да', 'нет')),
    CONSTRAINT CK_area_properties_FORMAT CHECK (area_properties > 0),
    CONSTRAINT CK_build_year_properties_FORMAT CHECK (
        build_year_properties BETWEEN 1800 AND EXTRACT(YEAR FROM CURRENT_DATE)
    ),
    CONSTRAINT CK_rooms_count_properties_FORMAT CHECK (rooms_count_properties >= 0),
    CONSTRAINT CK_address_properties_FORMAT CHECK (LENGTH(address_properties) <= 100),
    CONSTRAINT CK_region_properties_FORMAT CHECK (LENGTH(region_properties) <= 50),
    CONSTRAINT CK_floor_properties_FORMAT CHECK (floor_properties >= 0),
    CONSTRAINT CK_total_floors_properties_FORMAT CHECK (total_floors_properties >= 0),
    CONSTRAINT CK_property_type_FORMAT CHECK (
        property_type IN ('квартира', 'дом', 'офис', 'участок')
    )
);

CREATE TABLE Deals (
    deal_id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    buyer_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    final_price NUMERIC(15,2) NOT NULL,
    deal_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    deal_date TIMESTAMP NOT NULL,
    description TEXT,
    CONSTRAINT FK_owner FOREIGN KEY (owner_id) REFERENCES Clients(client_id),
    CONSTRAINT FK_buyer FOREIGN KEY (buyer_id) REFERENCES Clients(client_id),
    CONSTRAINT FK_property FOREIGN KEY (property_id) REFERENCES Properties(property_id),
    CONSTRAINT FK_agent FOREIGN KEY (agent_id) REFERENCES Agents(agent_id),
    CONSTRAINT CK_final_price_positive CHECK (final_price > 0),
    CONSTRAINT CK_deal_type_valid CHECK (deal_type IN ('продажа', 'аренда')),
    CONSTRAINT CK_status_valid CHECK (status IN ('в процессе', 'завершена', 'отменена'))
);

CREATE TABLE Documents (
    document_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    passport_series VARCHAR(6) NOT NULL,
    passport_number VARCHAR(4) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(20) NOT NULL,
    middle_name VARCHAR(50) NOT NULL,
    issued_by VARCHAR(100) NOT NULL,
    issue_date DATE NOT NULL,
    CONSTRAINT FK_client FOREIGN KEY (client_id) REFERENCES Clients(client_id),
    CONSTRAINT UK_passport UNIQUE (passport_series, passport_number),
    CONSTRAINT CK_last_name_FORMAT CHECK (
        last_name ~ '^[А-Яа-яЁё\s]+$' AND last_name !~ '\d'
    ),
    CONSTRAINT CK_first_name_FORMAT CHECK (
        first_name ~ '^[А-Яа-яЁё\s]+$' AND first_name !~ '\d'
    ),
    CONSTRAINT CK_middle_name_FORMAT CHECK (
        middle_name ~ '^[А-Яа-яЁё\s]+$' AND middle_name !~ '\d'
    ),
    CONSTRAINT CK_issued_by_FORMAT CHECK (
        issued_by ~ '^[А-Яа-яЁё\s\.\-]+$' AND issued_by !~ '\d'
    )
);

INSERT INTO Clients (name_client, client_type, phone_number, email)
VALUES
    ('Иван', 'Продавец', '+79161234567', 'ivan.petrov@example.com'),
    ('Анна', 'Покупатель', '+79259876543', 'anna.smirnova@example.com'),
    ('Дмитрий', 'Арендодатель', '+79031112233', 'd.orlov.rent@example.com'),
    ('Елена', 'Арендатор', '+79174445566', 'elena.lease@example.com'),
    ('Сергей', 'Покупатель', '+79998887766', 's.volkov.buy@example.com');

INSERT INTO Agents (
    name_agent, surname_agent, patronymic_agent, work_experience,
    phone_number_agent, email_agent, password_agent
)
VALUES
    ('Алексей', 'Иванов', 'Петрович', 5, '+79161234567', 'a.ivanov@realtor.com', '$2b$12$KIXzWkXhUeQjJZVnqF1y.eJZVnqF1y.eJZVnqF1y.eJZVnqF1y.e'),
    ('Елена', 'Смирнова', 'Дмитриевна', 8, '+79259876543', 'e.smirnova@realtor.com', '$2b$12$KIXzWkXhUeQjJZVnqF1y.eJZVnqF1y.eJZVnqF1y.eJZVnqF1y.e'),
    ('Дмитрий', 'Козлов', 'Александрович', 3, '+79031112233', 'd.kozlov@realtor.com', '$2b$12$KIXzWkXhUeQjJZVnqF1y.eJZVnqF1y.eJZVnqF1y.eJZVnqF1y.e'),
    ('Ольга', 'Попова', 'Владимировна', 12, '+79174445566', 'o.popova@realtor.com', '$2b$12$KIXzWkXhUeQjJZVnqF1y.eJZVnqF1y.eJZVnqF1y.eJZVnqF1y.e'),
    ('Сергей', 'Морозов', 'Николаевич', 1, '+79998887766', 's.morozov@realtor.com', '$2b$12$KIXzWkXhUeQjJZVnqF1y.eJZVnqF1y.eJZVnqF1y.eJZVnqF1y.e');

INSERT INTO Requests (
    client_id, agent_id, price_request, region_request,
    area_request, rooms_count_request, funds_request
)
VALUES
    (1, 1, 12500000.00, 'Московский', 85.50, 3, 13000000.00),
    (2, 2, 8900000.00, 'Северный', 60.20, 2, 9500000.00),
    (3, 3, 25000000.00, 'Приморский', 120.00, 4, 27000000.00),
    (4, 4, 6500000.00, 'Южный', 45.80, 1, 7000000.00),
    (5, 5, 18000000.00, 'Центральный', 95.00, 3, 19000000.00);

INSERT INTO Properties (
    price_properties, lift_properties, territory_comfort_properties,
    area_properties, build_year_properties, rooms_count_properties,
    address_properties, region_properties, legal_aspects_properties,
    floor_properties, total_floors_properties, owner_id, property_type
)
VALUES
    (12500000.00, 'да', 'Закрытая территория, парковка', 85.50, 2015, 3, 'ул. Ленина, д. 45', 'Московский', 'Юридически чист', 5, 9, 1, 'квартира'),
    (8900000.00, 'нет', 'Общая парковка', 60.20, 1998, 2, 'пр. Мира, д. 12', 'Северный', 'Имеет ограничения', 3, 5, 2, 'квартира'),
    (25000000.00, 'да', 'Охраняемый участок, бассейн', 120.00, 2020, 4, 'ш. Энтузиастов, д. 78', 'Приморский', 'Юридически чист', 1, 1, 3, 'дом');

INSERT INTO Deals (
    owner_id, buyer_id, property_id, agent_id,
    final_price, deal_type, status, deal_date, description
)
VALUES
    (1, 2, 1, 1, 12500000.00, 'продажа', 'завершена', '2025-03-15 14:30:00', 'Продажа квартиры'),
    (3, 1, 3, 2, 25000000.00, 'продажа', 'в процессе', '2026-01-10 10:00:00', 'Дом в Приморском');

INSERT INTO Documents (
    client_id, passport_series, passport_number,
    last_name, first_name, middle_name, issued_by, issue_date
)
VALUES
    (1, '123456', '7890', 'Петров', 'Иван', 'Петрович', 'УФМС по г. Москва', '2020-05-15'),
    (2, '234567', '8901', 'Смирнова', 'Анна', 'Дмитриевна', 'УФМС по г. Санкт-Петербург', '2021-03-22');

CREATE OR REPLACE FUNCTION mark_property_as_sold()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'завершена' THEN
        UPDATE Properties 
        SET is_available = false 
        WHERE property_id = NEW.property_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mark_property_as_sold
AFTER INSERT OR UPDATE ON Deals
FOR EACH ROW
EXECUTE FUNCTION mark_property_as_sold();

CREATE ROLE client_role;
CREATE ROLE agent_role;
CREATE ROLE admin_role;
CREATE ROLE hr_role;

GRANT SELECT ON Clients TO client_role;
GRANT INSERT, UPDATE ON Clients TO client_role;
GRANT SELECT ON Properties TO client_role;
GRANT SELECT, INSERT, UPDATE ON Requests TO client_role;
GRANT SELECT ON Deals TO client_role;
GRANT SELECT, INSERT ON Documents TO client_role;
GRANT SELECT ON Agents TO client_role;

GRANT SELECT, INSERT, UPDATE ON Clients TO agent_role;
GRANT SELECT, INSERT, UPDATE ON Properties TO agent_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Requests TO agent_role;
GRANT SELECT, INSERT, UPDATE ON Deals TO agent_role;
GRANT SELECT, UPDATE ON Agents TO agent_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON Clients TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Properties TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Requests TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Deals TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Documents TO admin_role;
GRANT SELECT ON Agents TO admin_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON Clients TO hr_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Documents TO hr_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Agents TO hr_role;

ALTER TABLE Clients ENABLE ROW LEVEL SECURITY;
CREATE POLICY client_own_data_policy ON Clients
FOR ALL USING (client_id = current_setting('app.current_client_id')::INTEGER);

ALTER TABLE Requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY request_own_data_policy ON Requests
FOR ALL USING (client_id = current_setting('app.current_client_id')::INTEGER);

ALTER TABLE Deals ENABLE ROW LEVEL SECURITY;
CREATE POLICY deal_own_data_policy ON Deals
FOR SELECT USING (
    owner_id = current_setting('app.current_client_id')::INTEGER OR
    buyer_id = current_setting('app.current_client_id')::INTEGER
);

ALTER TABLE Documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY document_own_data_policy ON Documents
FOR ALL USING (client_id = current_setting('app.current_client_id')::INTEGER);

ALTER TABLE Agents ENABLE ROW LEVEL SECURITY;
CREATE POLICY agent_own_data_policy ON Agents
FOR ALL USING (agent_id = current_setting('app.current_agent_id')::INTEGER);

CREATE USER client_user WITH PASSWORD 'client123';
CREATE USER agent_user WITH PASSWORD 'agent123';
CREATE USER admin_user WITH PASSWORD 'admin123';
CREATE USER hr_user WITH PASSWORD 'hr123';

GRANT client_role TO client_user;
GRANT agent_role TO agent_user;
GRANT admin_role TO admin_user;
GRANT hr_role TO hr_user;

GRANT CONNECT ON DATABASE kyrswork TO client_user, agent_user, admin_user, hr_user;
GRANT USAGE ON SCHEMA public TO client_user, agent_user, admin_user, hr_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO client_user, agent_user, admin_user, hr_user;