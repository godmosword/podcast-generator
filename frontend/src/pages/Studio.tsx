import { ArrowLeft, ArrowRight, Sparkles, Wand2 } from "lucide-react";
import { AudioSettings } from "../components/AudioSettings";
import { ClassicsSelector } from "../components/ClassicsSelector";
import { GenerateProgress } from "../components/GenerateProgress";
import { HostCountPicker } from "../components/HostCountPicker";
import { StepNav } from "../components/StepNav";
import { VoiceSlotRow } from "../components/VoiceSlotRow";
import { useStudio } from "../hooks/useStudio";

export function Studio() {
  const studio = useStudio();

  return (
    <main className="studio-shell">
      <header className="topbar">
        <div className="brand-mark">
          <Sparkles size={21} />
        </div>
        <div>
          <h1>Wavescript</h1>
          <p>Studio</p>
        </div>
        <button className="primary-action" onClick={studio.generate} type="button">
          <Wand2 size={18} />
          <span>生成</span>
        </button>
      </header>

      <StepNav current={studio.step} onSelect={studio.setStep} />

      <div className="workspace">
        <aside className="summary-rail">
          <div className="summary-block">
            <span>字數</span>
            <strong>{studio.stats.chars.toLocaleString()}</strong>
          </div>
          <div className="summary-block accent-green">
            <span>估時</span>
            <strong>{studio.stats.minutes}m</strong>
          </div>
          <div className="summary-block accent-rose">
            <span>主持</span>
            <strong>{studio.hostCount}</strong>
          </div>
          <div className="detected-list">
            {studio.visibleSlots.map((slot) => (
              <span key={slot.id}>{slot.role || `主持人${slot.id}`}</span>
            ))}
          </div>
        </aside>

        <div className="main-flow">
          {studio.step === 1 && (
            <ClassicsSelector
              chars={studio.stats.chars}
              classicsError={studio.classicsError}
              classicsLoading={studio.classicsLoading}
              classics={studio.filteredClassics}
              detectedHosts={studio.stats.detectedHosts}
              storyFilter={studio.storyFilter}
              minutes={studio.stats.minutes}
              mode={studio.scriptMode}
              onStoryFilter={studio.setStoryFilter}
              onModeChange={studio.setScriptMode}
              onScriptChange={studio.setScript}
              onSelectClassic={studio.selectClassic}
              script={studio.script}
              selectedClassicId={studio.selectedClassicId}
            />
          )}

          {studio.step === 2 && (
            <section className="panel hosts-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Step 2</p>
                  <h2>主持人</h2>
                </div>
                <HostCountPicker onChange={studio.setHostCount} value={studio.hostCount} />
              </div>

              <div className="voice-list">
                {studio.visibleSlots.map((slot) => (
                  <VoiceSlotRow
                    key={slot.id}
                    onChange={(changes) => studio.updateSlot(slot.id, changes)}
                    onPreview={() => studio.previewSlot(slot.id)}
                    slot={slot}
                  />
                ))}
              </div>
            </section>
          )}

          {studio.step === 3 && (
            <AudioSettings
              bgmEnabled={studio.bgmEnabled}
              bgmFadeMs={studio.bgmFadeMs}
              bgmTracks={studio.bgmTracks}
              bgmVolumeDb={studio.bgmVolumeDb}
              format={studio.format}
              pauseMs={studio.pauseMs}
              previewBgm={studio.previewBgm}
              selectedBgmId={studio.selectedBgmId}
              setBgmEnabled={studio.setBgmEnabled}
              setBgmFadeMs={studio.setBgmFadeMs}
              setBgmVolumeDb={studio.setBgmVolumeDb}
              setFormat={studio.setFormat}
              setPauseMs={studio.setPauseMs}
              setSelectedBgmId={studio.setSelectedBgmId}
              setSpeed={studio.setSpeed}
              speed={studio.speed}
            />
          )}

          {studio.step === 4 && (
            <GenerateProgress
              downloadUrl={studio.downloadUrl}
              error={studio.error}
              format={studio.format}
              isGenerating={studio.isGenerating}
              message={studio.statusMessage}
              progress={studio.progress}
            />
          )}

          <footer className="flow-controls">
            <button disabled={studio.step === 1} onClick={() => studio.setStep(Math.max(1, studio.step - 1))} type="button">
              <ArrowLeft size={18} />
              <span>上一步</span>
            </button>
            {studio.step < 4 ? (
              <button className="next-button" onClick={() => studio.setStep(Math.min(4, studio.step + 1))} type="button">
                <span>下一步</span>
                <ArrowRight size={18} />
              </button>
            ) : (
              <button className="next-button" onClick={studio.generate} type="button">
                <span>重新生成</span>
                <Wand2 size={18} />
              </button>
            )}
          </footer>
        </div>
      </div>
    </main>
  );
}
