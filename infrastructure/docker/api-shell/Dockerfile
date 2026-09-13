# Python 3.13.7 slim Bookworm; immutable base manifest digest.
FROM python@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d

COPY api_shell.py /opt/lengeas/api_shell.py

USER 65532:65532
EXPOSE 8000
ENTRYPOINT ["python", "/opt/lengeas/api_shell.py"]
