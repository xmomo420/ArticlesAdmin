-- Table pour représenter les utilisateurs de l'application
CREATE TABLE utilisateur (
    id INTEGER PRIMARY KEY,
    prenom TEXT,
    nom TEXT,
    identifiant TEXT,
    courriel TEXT,
    hach TEXT,
    salt TEXT,
    photo_profil BLOB
);

-- Table pour représenter les articles de l'application
CREATE TABLE article (
    identifiant TEXT PRIMARY KEY,
    titre TEXT,
    auteur_id INTEGER,
    date_publication DATE,
    contenu TEXT,
    est_html INTEGER,
    FOREIGN KEY (auteur_id) REFERENCES utilisateur(id)
);

-- Table pour représenter les sessions
CREATE TABLE session (
  id_session VARCHAR(32) PRIMARY KEY,
  utilisateur VARCHAR(25)
);
