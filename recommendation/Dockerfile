FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel

# 1. 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y git vim sudo curl gcc make dumb-init ffmpeg bash

# a안. Conda 환경 생성 및 faiss-gpu 설치
RUN conda create -n meta-convention python=3.12.4 -y && \
    /bin/bash -c "source activate meta-convention" && \
    conda install -c pytorch faiss-gpu -y

# b안. Conda 환경 생성 및 faiss-cpu 경우
# RUN conda create -n meta-convention python=3.12.4 -y && \
#     /bin/bash -c "source activate meta-convention" && \
#     conda install -c pytorch faiss-cpu -y

# 3. Poetry 설치
RUN pip install poetry

# 4. 작업 디렉토리 설정 및 pyproject.toml 복사
WORKDIR /app/srcs
COPY pyproject.toml ./

# 5. Poetry 설정 및 종속성 설치
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# 6. 소스 코드 복사
COPY . .

# 7. 엔트리포인트 및 CMD 설정
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=3000"]