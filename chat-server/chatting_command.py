ERROR_FATAL = {"type": "server.error", "code": 1}
ERROR_NO_ORG = {"type": "server.error", "code": 2}
ERROR_DUP_REQ = {"type": "server.error", "code": 3}
ERROR_REQ_PARAM = {"type": "server.error", "code": 4}

async def command(llm, message):
    print(message["type"] + "\n", flush=True)
    llm.log("< " + message["type"])
    if message["type"] == "config.update":
        org_id = message.get("org")
        user_id = message.get("userid", "none")
        lang = message.get("lang", "ko")
        if not org_id:
            await llm.ws.send_json(ERROR_REQ_PARAM)
        else:
            await llm.set_org(user_id, lang, org_id)

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
        text = message.get("text", None)
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