package travelbuddy.authservice.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import travelbuddy.authservice.model.Credential;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface CredentialRepository extends JpaRepository<Credential, UUID> {
  // Spring Data JPA is magic. Just by naming this method "findByEmail",
  // it automatically writes the SQL query: SELECT * FROM credentials WHERE email = ?
  Optional<Credential> findByEmail(String email);
}