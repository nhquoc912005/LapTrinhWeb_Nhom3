import datetime
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
import cryptography.hazmat.primitives.serialization.pkcs12 as pkcs12

def create_self_signed_cert(cert_dir="apps/core/certs", pfx_filename="dummy_cert.pfx", password=b"123456"):
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    
    pfx_path = os.path.join(cert_dir, pfx_filename)
    if os.path.exists(pfx_path):
        print(f"File {pfx_path} already exists. Skipping.")
        return

    # Generate our key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Various details about who we are. For a self-signed certificate the
    # subject and issuer are always the same.
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"VN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Da Nang"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Da Nang"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"QLVB Nhom3"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"QLVB Dummy Signer"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Our certificate will be valid for 10 years
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    # Sign our certificate with our private key
    ).sign(private_key, hashes.SHA256())

    # Create PKCS12 file (PFX)
    encryption = serialization.BestAvailableEncryption(password)
    pfx_data = pkcs12.serialize_key_and_certificates(
        b"dummy_cert", private_key, cert, None, encryption
    )

    with open(pfx_path, "wb") as f:
        f.write(pfx_data)
    
    print(f"Created {pfx_path}")

if __name__ == "__main__":
    create_self_signed_cert()
