# Remove existing dangling docker-images
if [ $(docker images --quiet --filter=dangling=true | wc -l) -gt 0 ]
then
  echo "Dangling docker image exists..."
  docker rmi -f $(docker images -f dangling=true -q)
fi

# Remove all running containers and networks
if [ $(docker ps -q -a | wc -l) -gt 0 ]
then
  echo "More than one container is running..."
  docker-compose down
fi

# Build docker containers
docker-compose up -d --build
echo "Build Complete"

# Check running state of all 3 containers
if [ $(docker ps --format "{{.Names}} {{.Status}}" | grep "Up" | wc -l) -ne 3 ]
then
  echo "Build error while running docker-compose"
  exit 1
else
  echo "Deploy Complete"
fi
