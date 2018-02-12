if [ "$1" == "build" ]
then
	echo "building..."
	echo "Building Python package"
	zip -r code.zip .
	echo "Complete"
else 
	echo ">>> We ♥️  Jerome <<<"
fi
