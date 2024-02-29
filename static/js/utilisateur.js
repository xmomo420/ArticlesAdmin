function afficherFormulaire() {
    // Afficher le formulaire
    document.getElementById('formulaire').style.display = 'block';

    // Masquer le message de succès
    const message = document.getElementById('message');
    if (message != null) {
        message.style.display = 'none';
    }
}

function masquerFormulaire() {
    // Masquer le formulaire
    document.getElementById('formulaire').style.display = 'none';
}

