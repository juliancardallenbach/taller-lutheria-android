# Como obtener el .apk (sin instalar nada en tu PC)

Este proyecto esta armado para compilarse solo, en la nube, usando GitHub
Actions. Vos solo subis el codigo y esperas.

## Paso 1: crear una cuenta de GitHub (si no tenes)
https://github.com/signup

## Paso 2: crear un repositorio nuevo
1. Entra a https://github.com/new
2. Ponele un nombre, por ejemplo `taller-lutheria-android`
3. Dejalo en "Public" (los minutos de compilacion son gratis en repos
   publicos) y creá el repositorio.

## Paso 3: subir esta carpeta al repositorio
La forma mas facil, sin usar la terminal: en la pagina del repositorio que
creaste, hace click en "Add file" -> "Upload files", y arrastra TODOS los
archivos y carpetas de esta carpeta `android_app` (incluida la carpeta
`.github` con el archivo `build-apk.yml` adentro; en algunos navegadores
hay que subir carpetas ocultas por separado, fijate que quede la ruta
`.github/workflows/build-apk.yml` en el repositorio).

Si preferis usar la terminal (con Git instalado):
```
cd android_app
git init
git add .
git commit -m "Primera version Android"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/taller-lutheria-android.git
git push -u origin main
```

## Paso 4: esperar a que compile
1. En la pagina de tu repositorio, anda a la pestaña "Actions".
2. Vas a ver un proceso llamado "Compilar APK" corriendo (tarda entre 15 y
   30 minutos la primera vez, porque tiene que descargar todo el Android
   SDK/NDK; las siguientes veces es mas rapido).
3. Cuando termine con un tilde verde, entra a ese resultado y al final de
   la pagina vas a ver un archivo para descargar llamado
   "taller-lutheria-apk". Ese es tu .apk, comprimido en un .zip.

## Paso 5: instalar el APK en tu celular
1. Descomprimi el .zip, adentro esta el archivo `.apk`.
2. Pasalo a tu celular Android (por cable, WhatsApp a vos mismo, Drive, etc).
3. Al abrirlo, Android va a pedirte permiso para "instalar apps de origen
   desconocido" la primera vez -> se lo das, y se instala.

## Si despues queres modificar el codigo
Cada vez que subas un cambio a la rama `main` de GitHub, el workflow se
vuelve a ejecutar solo y te genera un .apk nuevo en "Actions".

## Nota sobre esta primera version
Es una base funcional (formulario, guardado en SQLite, lista con busqueda,
generacion de PDF, apertura de WhatsApp con el mensaje armado, boton de
pagado). No incluye todavia: impresion del ticket termico por Bluetooth
(cada impresora portatil usa su propia libreria), ni el ordenamiento por
columnas ni la exportacion a Excel que tiene la version de Windows —
esas se pueden ir sumando despues de probar que esta base funciona bien
en tu celular.
