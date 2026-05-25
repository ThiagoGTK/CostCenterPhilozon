import { useState } from "react";
import { useWorkflows, useIniciarWorkflow, useEnviarWorkflow, useAprovarWorkflow, useReprovarWorkflow } from "../hooks/useWorkflow";
import { useVersoes } from "../hooks/useDimensoes";
import { WorkflowItem } from "../services/api";
import styles from "./PageGeneric.module.css";
import wfStyles from "./Workflow.module.css";

const ID_EMPRESA_PADRAO = 1;

const STATUS_COLORS: Record<string, string> = {
  RASCUNHO: wfStyles.rascunho,
  ENVIADO: wfStyles.enviado,
  APROVADO: wfStyles.aprovado,
  REPROVADO: wfStyles.reprovado,
};

const STATUS_LABELS: Record<string, string> = {
  RASCUNHO: "Rascunho",
  ENVIADO: "Aguardando aprovação",
  APROVADO: "Aprovado",
  REPROVADO: "Reprovado",
};

type ModalTipo = "iniciar" | "enviar" | "aprovar" | "reprovar" | null;

interface ModalState {
  tipo: ModalTipo;
  wfId?: number;
  wfLabel?: string;
}

export default function Workflow() {
  const anoAtual = new Date().getFullYear();
  const [ano, setAno] = useState(anoAtual);

  // Modal state
  const [modal, setModal] = useState<ModalState>({ tipo: null });
  const [nome, setNome] = useState("");
  const [idVersaoNova, setIdVersaoNova] = useState<number | "">("");
  const [comentario, setComentario] = useState("");
  const [erroModal, setErroModal] = useState("");

  const { data: workflows = [], isLoading, isError } = useWorkflows(ano);
  const { data: versoes = [] } = useVersoes(ano);

  const iniciar = useIniciarWorkflow();
  const enviar = useEnviarWorkflow();
  const aprovar = useAprovarWorkflow();
  const reprovar = useReprovarWorkflow();

  // Versões que ainda não têm workflow ativo (RASCUNHO ou ENVIADO)
  const idsComWorkflowAtivo = new Set(
    workflows
      .filter((w) => w.status === "RASCUNHO" || w.status === "ENVIADO")
      .map((w) => w.id_versao)
  );
  const versoesSemWorkflow = versoes.filter((v) => !idsComWorkflowAtivo.has(v.id));

  function abrirModal(tipo: ModalTipo, wf?: WorkflowItem) {
    setModal({ tipo, wfId: wf?.id, wfLabel: wf ? `${wf.versao_nome} — ${wf.empresa_nome}` : undefined });
    setNome("");
    setComentario("");
    setErroModal("");
    setIdVersaoNova("");
  }

  function fecharModal() {
    setModal({ tipo: null });
  }

  async function handleConfirmar() {
    setErroModal("");

    if (!nome.trim()) {
      setErroModal("Informe seu nome.");
      return;
    }

    try {
      if (modal.tipo === "iniciar") {
        if (!idVersaoNova) {
          setErroModal("Selecione a versão.");
          return;
        }
        await iniciar.mutateAsync({
          id_versao: Number(idVersaoNova),
          id_empresa: ID_EMPRESA_PADRAO,
          criado_por: nome.trim(),
        });
      } else if (modal.tipo === "enviar" && modal.wfId) {
        await enviar.mutateAsync({ id: modal.wfId, payload: { enviado_por: nome.trim() } });
      } else if (modal.tipo === "aprovar" && modal.wfId) {
        await aprovar.mutateAsync({
          id: modal.wfId,
          payload: { aprovado_por: nome.trim(), comentario: comentario.trim() || undefined },
        });
      } else if (modal.tipo === "reprovar" && modal.wfId) {
        if (!comentario.trim()) {
          setErroModal("O motivo de reprovação é obrigatório.");
          return;
        }
        await reprovar.mutateAsync({
          id: modal.wfId,
          payload: { reprovado_por: nome.trim(), comentario: comentario.trim() },
        });
      }
      fecharModal();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErroModal(msg ?? "Erro ao executar a ação. Tente novamente.");
    }
  }

  const isPending =
    iniciar.isPending || enviar.isPending || aprovar.isPending || reprovar.isPending;

  function formatData(iso?: string) {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  const titulosModal: Record<string, string> = {
    iniciar: "Iniciar processo de aprovação",
    enviar: "Enviar para revisão",
    aprovar: "Aprovar orçamento",
    reprovar: "Reprovar orçamento",
  };

  const confirmarLabels: Record<string, string> = {
    iniciar: "Iniciar",
    enviar: "Enviar para revisão",
    aprovar: "Aprovar",
    reprovar: "Reprovar",
  };

  return (
    <div className={styles.page}>
      {/* Filtros */}
      <div className={styles.filterBar}>
        <label className={styles.filterItem}>
          <span>Ano</span>
          <select value={ano} onChange={(e) => setAno(Number(e.target.value))}>
            {[anoAtual - 1, anoAtual, anoAtual + 1].map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </label>
        <div style={{ marginLeft: "auto" }}>
          {versoesSemWorkflow.length > 0 && (
            <button
              className={styles.btnPrimary}
              onClick={() => abrirModal("iniciar")}
            >
              + Iniciar processo
            </button>
          )}
        </div>
      </div>

      {/* Tabela principal */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>
            Fila de Aprovação de Orçamentos — {ano}
          </span>
          <span style={{ fontSize: 13, color: "#64748b" }}>
            {workflows.length} registro{workflows.length !== 1 ? "s" : ""}
          </span>
        </div>

        {isLoading && <div className={styles.loadingMsg}>Carregando...</div>}
        {isError && <div className={styles.errorMsg}>Erro ao carregar workflows. Verifique a API.</div>}

        {!isLoading && (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Versão</th>
                  <th>Empresa</th>
                  <th>Status</th>
                  <th>Responsável</th>
                  <th>Data</th>
                  <th>Comentário</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {workflows.length === 0 ? (
                  <tr>
                    <td colSpan={7} className={styles.emptyRow}>
                      Nenhum workflow registrado para {ano}.{" "}
                      {versoesSemWorkflow.length > 0 && (
                        <button
                          style={{ background: "none", border: "none", color: "#2563eb", cursor: "pointer", fontSize: 13 }}
                          onClick={() => abrirModal("iniciar")}
                        >
                          Iniciar processo →
                        </button>
                      )}
                    </td>
                  </tr>
                ) : (
                  workflows.map((wf) => (
                    <tr key={wf.id}>
                      <td>
                        <strong>{wf.versao_nome}</strong>
                        <div className={wfStyles.decisaoInfo}>{wf.versao_ano}</div>
                      </td>
                      <td>{wf.empresa_nome}</td>
                      <td>
                        <span className={`${wfStyles.badge} ${STATUS_COLORS[wf.status]}`}>
                          {STATUS_LABELS[wf.status]}
                        </span>
                      </td>
                      <td style={{ fontSize: 13 }}>
                        {wf.status === "APROVADO" && wf.aprovado_por && (
                          <span>{wf.aprovado_por}</span>
                        )}
                        {wf.status === "REPROVADO" && wf.reprovado_por && (
                          <span>{wf.reprovado_por}</span>
                        )}
                        {wf.status === "ENVIADO" && wf.enviado_por && (
                          <span>{wf.enviado_por}</span>
                        )}
                        {wf.status === "RASCUNHO" && (
                          <span style={{ color: "#94a3b8" }}>{wf.criado_por}</span>
                        )}
                      </td>
                      <td style={{ fontSize: 12, color: "#64748b", whiteSpace: "nowrap" }}>
                        {wf.status === "APROVADO" || wf.status === "REPROVADO"
                          ? formatData(wf.data_decisao)
                          : wf.status === "ENVIADO"
                          ? formatData(wf.data_envio)
                          : formatData(wf.criado_em)}
                      </td>
                      <td>
                        {wf.comentario && (
                          <span className={wfStyles.comentarioTexto} title={wf.comentario}>
                            {wf.comentario}
                          </span>
                        )}
                      </td>
                      <td>
                        <div className={wfStyles.acoes}>
                          {wf.status === "RASCUNHO" && (
                            <button
                              className={wfStyles.btnEnviar}
                              onClick={() => abrirModal("enviar", wf)}
                            >
                              Enviar para revisão
                            </button>
                          )}
                          {wf.status === "ENVIADO" && (
                            <>
                              <button
                                className={wfStyles.btnAprovar}
                                onClick={() => abrirModal("aprovar", wf)}
                              >
                                Aprovar
                              </button>
                              <button
                                className={wfStyles.btnReprovar}
                                onClick={() => abrirModal("reprovar", wf)}
                              >
                                Reprovar
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal universal */}
      {modal.tipo && (
        <div className={wfStyles.overlay} onClick={fecharModal}>
          <div className={wfStyles.modal} onClick={(e) => e.stopPropagation()}>
            <h3 className={wfStyles.modalTitle}>
              {titulosModal[modal.tipo]}
            </h3>

            {/* Meta info do workflow alvo */}
            {modal.wfLabel && (
              <div className={wfStyles.modalMeta}>{modal.wfLabel}</div>
            )}

            {/* Seletor de versão (apenas em "iniciar") */}
            {modal.tipo === "iniciar" && (
              <label className={wfStyles.modalField}>
                <span>Versão</span>
                <select
                  value={idVersaoNova}
                  onChange={(e) => setIdVersaoNova(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="">— selecione —</option>
                  {versoesSemWorkflow.map((v) => (
                    <option key={v.id} value={v.id}>{v.nome}</option>
                  ))}
                </select>
              </label>
            )}

            {/* Nome do responsável */}
            <label className={wfStyles.modalField}>
              <span>Seu nome</span>
              <input
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                placeholder="Ex: Ana Silva"
                autoFocus
              />
            </label>

            {/* Comentário (opcional em aprovar, obrigatório em reprovar) */}
            {(modal.tipo === "aprovar" || modal.tipo === "reprovar") && (
              <label className={wfStyles.modalField}>
                <span>
                  {modal.tipo === "reprovar"
                    ? "Motivo da reprovação (obrigatório)"
                    : "Comentário (opcional)"}
                </span>
                <textarea
                  value={comentario}
                  onChange={(e) => setComentario(e.target.value)}
                  placeholder={
                    modal.tipo === "reprovar"
                      ? "Descreva o motivo da reprovação..."
                      : "Observações sobre a aprovação..."
                  }
                />
              </label>
            )}

            {erroModal && <p className={wfStyles.errorInline}>{erroModal}</p>}

            <div className={wfStyles.modalActions}>
              <button className={styles.btnSecondary} onClick={fecharModal} disabled={isPending}>
                Cancelar
              </button>
              <button
                className={
                  modal.tipo === "reprovar"
                    ? wfStyles.btnReprovar
                    : modal.tipo === "aprovar"
                    ? wfStyles.btnAprovar
                    : styles.btnPrimary
                }
                onClick={handleConfirmar}
                disabled={isPending}
              >
                {isPending ? "Aguarde..." : confirmarLabels[modal.tipo]}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
