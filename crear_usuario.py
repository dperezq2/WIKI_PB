from app import app, db, User  # Importamos la aplicación y la base de datos

with app.app_context():
    nuevo_usuario = User (
        nombre1="José Alfonso",
        apellido1="Ramírez Mendoza ",
        correo="j.mendoza@paloblancofresh.com"
    )
    nuevo_usuario.set_password("Dougl@s2024")

    db.session.add(nuevo_usuario)
    db.session.commit()

    print("✅ Usuario creado correctamente.")