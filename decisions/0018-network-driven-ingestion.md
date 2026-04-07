# 0018. Network-driven ingestion

Date: 2026-04-06
Status: accepted

## Context

The platform's credibility depends on the quality of its knowledge graph. The knowledge graph is only as good as the records that feed it. This raises a fundamental question: who decides what gets ingested?

Open ingestion - accepting any submitted material - is vulnerable to deliberate manipulation. A state-level actor with an interest in controlling the narrative around unidentified anomalous phenomena could manufacture credible-looking documents, create professional media placements, or flood the system with misleading material. Because the platform's methodology is public (decision 0004), an adversary can study the scoring system and craft material designed to game it.

Centralised editorial control - one person deciding what gets in - creates a single point of failure and contradicts the platform's commitment to transparency. It also doesn't scale.

The domain has an additional structural problem. Almost all information is testimony. There is very little independently verifiable physical evidence. The scoring system can track corroboration, contradictions, and source track records, but it cannot determine whether testimony is true. Official sources (governments, military agencies) have a documented history of issuing denials that are later contradicted by primary documents and sworn testimony. Traditional authority does not correlate with reliability in this domain.

## Decision

Ingestion is driven by the network of people and references already in the knowledge graph, not by external editorial decisions.

### How it works

**Seed.** The knowledge graph starts with a small set of well-known figures who have gone on the public record: witnesses who have testified under oath, whistleblowers who have made formal disclosures, and investigative journalists who have published verified reporting. The initial seed is a deliberate human choice, but it is small, defensible, and documented.

**Fan out through people.** The infrastructure extraction pass (see digester pipeline) identifies who the existing figures talk to, interview, reference, and collaborate with. When multiple existing sources engage with a new person, that person's records become candidates for ingestion.

**Fan out through records.** When ingested records reference specific documents, reports, investigations, or other material, those become candidates for ingestion. A whistleblower mentioning a classified programme report, a journalist citing a Freedom of Information Act document, or a congressional hearing referencing an inspector general finding - these references point the system toward new material.

**The network is the boundary.** A record gets ingested because it is connected to existing material through people or references. The platform follows the network that the sources themselves have built. Investigative journalists do the filtering. Freedom of Information Act researchers surface the documents. Whistleblowers decide what to disclose. The platform collates and assembles rather than making those editorial decisions itself.

### What this means for new contributors

When someone joins the project and proposes records for ingestion, the network provides a natural check. Proposed material should be connected to the existing graph through people or references. Material with no connection to anything in the graph is not automatically rejected, but the lack of connection is a flag that requires justification.

### What this means for adversarial content

A state-level actor wanting to inject misleading material into the knowledge graph would need to manufacture content that gets referenced by people already in the trusted network. They cannot simply flood the system with documents, because unconnected material does not enter the graph. This is harder to game than an open submission model or an algorithmic filter, because it relies on the social network of real people who have staked their reputations on their public statements.

This does not make the system immune to manipulation. A sufficiently determined actor could compromise individuals within the network, or create material convincing enough that existing sources reference it. But it raises the bar significantly compared to open ingestion.

### Limitations

The scoring system does not tell readers what is true. It tells them what the weight of testimony looks like - who said what, whether it is corroborated, whether it has been contradicted, and what the source's track record shows. The platform is a tool for navigating testimony, not a truth machine. This limitation is stated clearly on the site's methodology page.

## Consequences

The platform does not need a human gatekeeper reviewing every record. The network determines what enters the system. The initial seed is the only purely editorial decision, and it is documented and open to scrutiny.

The platform inherits the biases and blind spots of its seed network. If the initial figures are predominantly American military and intelligence sources, the early knowledge graph will reflect that perspective. As the network fans out to international sources, researchers, and witnesses from other countries, the graph broadens. This is a known limitation of the approach and is addressed by deliberately including international figures in the seed where possible.

New whistleblowers or witnesses who have no connection to the existing network face a cold-start problem. They cannot be discovered through infrastructure extraction because nobody has mentioned them yet. In practice, significant new entrants tend to be surfaced quickly by investigative journalists and researchers already in the network. Truly isolated witnesses may need a separate submission pathway in a later phase.
