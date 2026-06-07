FROM eclipse-temurin:21-jdk AS build
WORKDIR /app

COPY backend-services/itinerary-service/mvnw .
COPY backend-services/itinerary-service/.mvn .mvn
COPY backend-services/itinerary-service/pom.xml .
COPY shared-proto ../../shared-proto

# Fix 1: Make the wrapper executable so Linux doesn't block it
RUN chmod +x ./mvnw

# Fix 2: Download dependencies FIRST. Docker will cache this layer!
RUN ./mvnw dependency:go-offline -B

# NOW copy the source code.
# If you change a Java file, Docker skips the download step above and starts here.
COPY backend-services/itinerary-service/src src

RUN ./mvnw -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

ENTRYPOINT ["java", "-jar", "app.jar"]