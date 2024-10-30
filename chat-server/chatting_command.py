ERROR_FATAL = {"type": "server.error", "code": 1}
ERROR_NO_ORG = {"type": "server.error", "code": 2}
ERROR_DUP_REQ = {"type": "server.error", "code": 3}
ERROR_REQ_PARAM = {"type": "server.error", "code": 4}

async def command(llm, message):
    print(message["type"] + "\n", flush=True)
    llm.log("< " + message["type"])
    if message["type"] == "config.update":
        org_id = message.get("org")
        if not org_id:
            await llm.ws.send_json(ERROR_REQ_PARAM)
        else:
            await llm.set_org(org_id)

    elif message["type"] == "buffer.add_audio":
        audio_data = message.get("audio")
        if not llm:
            await llm.ws.send_json(ERROR_NO_ORG)
        else:
            await llm.add_audio(audio_data)

    elif message["type"] == "buffer.clear_audio":
        if not llm:
            await llm.ws.send_json(ERROR_NO_ORG)
        else:
            await llm.clear_audio()

    elif message["type"] == "generate.text_audio":
        if not llm.is_gen_ready():
            await llm.response_error(ERROR_DUP_REQ)
            return
        text = message.get("text", "")
        text += "😄 (유저는 당신에 대해 매우 호의적입니다. 😄😄😄 자주 웃으며 높은 톤으로 생동감 있고 친근하게 대답해주세요. 짧고 간결하게 15초 내외로 답해주세요.)"
        if text:
            await llm.add_text("user", text)
        await llm.generate(["text", "audio"])

    elif message["type"] == "generate.only_text":
        if not llm.is_gen_ready():
            await llm.response_error(ERROR_DUP_REQ)
            return
        text = message.get("text", None)
        if text:
            await llm.add_text("user", text)
        await llm.generate(["text"])

    elif message["type"] == "generate.cancel":
        await llm.cancel()
    llm.log("> complete " + message["type"])