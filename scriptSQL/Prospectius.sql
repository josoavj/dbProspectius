/*
    Auteur: Josoa (josoavj sur GitHub)
    Ce script est la source de la base de données du projet Prospectius
    Veuillez vous réferer à la documentation ou envoyer un mail à l'auteur si vous avez besoin d'aide
*/

-- Suppression complète de la base de données
DROP DATABASE IF EXISTS Prospectius;

-- Création de la DB
CREATE DATABASE Prospectius;
USE Prospectius;

-- Table Compte
CREATE TABLE Account (
                         id_compte INT AUTO_INCREMENT PRIMARY KEY,
                         nom VARCHAR(70) NOT NULL,
                         prenom VARCHAR(70) NOT NULL,
                         email VARCHAR(100) NOT NULL UNIQUE,
                         username VARCHAR(50) NOT NULL UNIQUE,
                         password VARCHAR(255) NOT NULL,
                         type_compte ENUM('Administrateur', 'Utilisateur') NOT NULL,
                         date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         UNIQUE (nom, prenom)
);

/*
    Pour la table Account:
    - Il est recommandé d'utiliser un mot de passe crypté: veuillez crypter votre mot de passe en fonction du techno ou langage utilisé
    - Le mot de passe ne doit pas contenir des informations sensibles (Informations personnelles)
    - Un seul compte Administrateur est requis.
    - Seul l'administrateur qui possède le droit de supprimer des comptes dans la base de données.
*/

-- Compte administrateur unique
DELIMITER $$

CREATE TRIGGER avant_ajout_compte
    BEFORE INSERT ON Account
    FOR EACH ROW
BEGIN
    IF NEW.type_compte = 'Administrateur' AND (SELECT COUNT(*) FROM Account WHERE type_compte = 'Administrateur') > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un compte Administrateur existe déjà.';
    END IF;
END$$

DELIMITER ;

-- Vérification du mail
DELIMITER $$

CREATE TRIGGER ajout_compte
    BEFORE INSERT ON Account
    FOR EACH ROW
BEGIN
    IF NEW.email NOT LIKE '%@%.%' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'L\'email doit contenir un "@" et un "."';
    END IF;
END$$

CREATE TRIGGER maj_compte
    BEFORE UPDATE ON Account
    FOR EACH ROW
BEGIN
    IF NEW.email NOT LIKE '%@%.%' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'L\'email doit contenir un "@" et un "."';
    END IF;
END$$

DELIMITER ;

-- Modification du type de compte
DELIMITER $$

CREATE TRIGGER avant_maj_compte
    BEFORE UPDATE ON Account
    FOR EACH ROW
BEGIN
    IF OLD.type_compte != NEW.type_compte THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Le type de compte ne peut pas être modifié.';
    END IF;
END$$

DELIMITER ;


-- Pour le mot de passe

DELIMITER $$

CREATE TRIGGER avant_ajout_password
    BEFORE INSERT ON Account
    FOR EACH ROW
BEGIN
    IF CHAR_LENGTH(NEW.password) < 8 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Le mot de passe doit contenir au moins 8 caractères.';
    END IF;
END$$

CREATE TRIGGER avant_maj_password
    BEFORE UPDATE ON Account
    FOR EACH ROW
BEGIN
    IF CHAR_LENGTH(NEW.password) < 8 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Le mot de passe doit contenir au moins 8 caractères.';
    END IF;
END$$

DELIMITER ;

-- Empêcher la suppression du dernier compte administrateur présent dans la base de données
DELIMITER $$

CREATE TRIGGER avant_suppression_compte_administrateur
    BEFORE DELETE ON Account
    FOR EACH ROW
BEGIN
    IF OLD.type_compte = 'Administrateur' AND (SELECT COUNT(*) FROM Account WHERE type_compte = 'Administrateur') = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La suppression du dernier compte Administrateur est interdite.';
    END IF;
END$$

DELIMITER ;

/*
    Modifié le 18 Octobre 2025
*/