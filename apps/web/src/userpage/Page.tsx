import { FormEvent, useState } from "react";

type ThbResponse = {
  meaning: string;
};

export default function Page() {
  const [sourceMessage, setSourceMessage] = useState("");
  const [context, setContext] = useState("");
  const [meaning, setMeaning] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedMessage = sourceMessage.trim();

    if (!trimmedMessage) {
      setError("请输入需要分析的内容。");
      return;
    }

    setLoading(true);
    setError(null);
    setMeaning(null);

    try {
      const response = await fetch("/api/v1/thb", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
        source_message: trimmedMessage,
        context: context.trim(),
        }),
      });

    //   if (!response.ok) {
    //     throw new Error(`请求失败：${response.status}`);
    //   }
      if (!response.ok) {
        const errorData = await response.json();

        throw new Error(
            `请求失败：${response.status}\n${JSON.stringify(errorData, null, 2)}`
        );
}

      const data = (await response.json()) as ThbResponse;

      if (!data.meaning) {
        throw new Error("接口没有返回 meaning。");
      }

      setMeaning(data.meaning);
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-100 px-8 py-12 text-zinc-900">
      <div className="mx-auto w-full max-w-5xl">
        <header className="mb-10">
          <h1 className="text-4xl font-semibold tracking-tight">THB</h1>

          <p className="mt-3 text-base leading-7 text-zinc-600">
            把你想处理的沟通内容放进来，我会帮你看看其中真正重要的是什么。
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="rounded-3xl border border-zinc-200 bg-white p-8 shadow-sm"
        >
          <div>
            <label
              htmlFor="source-message"
              className="text-sm font-medium text-zinc-900"
            >
              原始内容
            </label>

            <p className="mt-1 text-sm text-zinc-500">
              可以直接粘贴聊天记录、邮件，或者描述发生了什么。
            </p>

            <textarea
              id="source-message"
              value={sourceMessage}
              onChange={(event) => setSourceMessage(event.target.value)}
              disabled={loading}
              rows={12}
              placeholder="把内容放在这里……"
              className="mt-4 w-full resize-y rounded-2xl border border-zinc-300 bg-white px-4 py-4 text-base leading-7 text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-4 focus:ring-zinc-100 disabled:cursor-not-allowed disabled:bg-zinc-50"
            />
          </div>

          <div className="mt-8">
            <label
              htmlFor="context"
              className="text-sm font-medium text-zinc-900"
            >
              背景补充
              <span className="ml-2 font-normal text-zinc-400">可选</span>
            </label>

            <p className="mt-1 text-sm text-zinc-500">
              如果有一些只有你知道的前因后果，可以补充在这里。
            </p>

            <textarea
              id="context"
              value={context}
              onChange={(event) => setContext(event.target.value)}
              disabled={loading}
              rows={5}
              placeholder="例如：之前发生过什么、双方是什么关系、你特别在意什么……"
              className="mt-4 w-full resize-y rounded-2xl border border-zinc-300 bg-white px-4 py-4 text-base leading-7 text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-4 focus:ring-zinc-100 disabled:cursor-not-allowed disabled:bg-zinc-50"
            />
          </div>

          {error && (
            <div
              role="alert"
              className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </div>
          )}

          <div className="mt-8 flex justify-end">
            <button
              type="submit"
              disabled={loading || !sourceMessage.trim()}
              className="min-w-32 rounded-xl bg-zinc-900 px-6 py-3 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:bg-zinc-300"
            >
              {loading ? "分析中……" : "开始分析"}
            </button>
          </div>
        </form>

        <section className="mt-8 rounded-3xl border border-zinc-200 bg-white p-8 shadow-sm">
          <div className="border-b border-zinc-100 pb-5">
            <h2 className="text-xl font-semibold tracking-tight">
              THB 看到了什么
            </h2>
          </div>

          <div className="min-h-40 pt-6">
            {loading && (
              <div className="flex min-h-32 items-center justify-center">
                <div className="text-sm text-zinc-500">正在分析，请稍等……</div>
              </div>
            )}

            {!loading && !meaning && (
              <div className="flex min-h-32 items-center justify-center">
                <p className="text-sm text-zinc-400">
                  分析结果会显示在这里。
                </p>
              </div>
            )}

            {!loading && meaning && (
              <p className="whitespace-pre-wrap text-base leading-8 text-zinc-800">
                {meaning}
              </p>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}