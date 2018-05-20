# if you need to add new packages / dependancies to the build you will need to do so with pip wheel
# - pip install image-resizer
# - pip wheel image-resizer
# - unzip image_resizer-0.1.1-py2-none-any.whl

# the above will install a dependancy called image resizer, then create a wheel file from it and then you unzip the newly created whl file.
# The below code will include the unzipped whl in the .zip payload

if [ "$1" == "build" ]
then
	echo "building..."
	echo "Building Python package"
	zip -r code.zip .
	echo "Complete"
else 
	echo ">>> We ♥️  Jerome <<<"
fi
